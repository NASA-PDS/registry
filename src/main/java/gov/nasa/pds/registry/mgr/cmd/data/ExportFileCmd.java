package gov.nasa.pds.registry.mgr.cmd.data;

import java.util.Map;

import org.apache.commons.cli.CommandLine;
import org.elasticsearch.client.Request;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestClient;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.common.es.client.EsUtils;
import gov.nasa.pds.registry.common.es.client.SearchResponseParser;
import gov.nasa.pds.registry.mgr.Constants;
import gov.nasa.pds.registry.mgr.cmd.CliCommand;
import gov.nasa.pds.registry.mgr.dao.RegistryRequestBuilder;
import gov.nasa.pds.registry.mgr.util.CloseUtils;
import gov.nasa.pds.registry.mgr.util.EmbeddedBlobExporter;


/**
 * CLI command to export a BLOB object from Elasticsearch into a file. 
 * 
 * @author karpenko
 */
public class ExportFileCmd implements CliCommand
{
    /**
     * Inner class to process search response from Elasticsearch API.
     * 
     * @author karpenko
     */
    private static class ResponseCB implements SearchResponseParser.Callback
    {
        private boolean found = false; 
        private String lidvid;
        private String filePath;
        
        /**
         * Constructor
         * @param lidvid LidVid of a document with BLOB
         * @param filePath File path to export BLOB to.
         */
        public ResponseCB(String lidvid, String filePath)
        {
            this.lidvid = lidvid;
            this.filePath = filePath;
        }
        
        
        @Override
        @SuppressWarnings("rawtypes")
        public void onRecord(String id, Object rec) throws Exception
        {
            found = true;
         
            Object blob = ((Map)rec).get(Constants.BLOB_FIELD);
            if(blob == null)
            {
                System.out.println("There is no BLOB in a document with LIDVID = " + lidvid);
                System.out.println("Probably embedded BLOB storage was not enabled when the document was created.");
                return;
            }

            EmbeddedBlobExporter.export(blob.toString(), filePath);
            System.out.println("Done");
        }
        
        
        public boolean found()
        {
            return found;
        }
        
    }
    
    
    /**
     * Constructor
     */
    public ExportFileCmd()
    {
    }
    
    
    @Override
    public void run(CommandLine cmdLine) throws Exception
    {
        if(cmdLine.hasOption("help"))
        {
            printHelp();
            return;
        }
        
        String esUrl = cmdLine.getOptionValue("es", "http://localhost:9200");
        String indexName = cmdLine.getOptionValue("index", Constants.DEFAULT_REGISTRY_INDEX);
        String authPath = cmdLine.getOptionValue("auth");
        
        // Lidvid
        String lidvid = cmdLine.getOptionValue("lidvid");
        if(lidvid == null) 
        {
            throw new Exception("Missing required parameter '-lidvid'");
        }
        
        // File path
        String filePath = cmdLine.getOptionValue("file");
        if(filePath == null) 
        {
            throw new Exception("Missing required parameter '-file'");
        }

        System.out.println("Elasticsearch URL: " + esUrl);
        System.out.println("            Index: " + indexName);
        System.out.println("           LIDVID: " + lidvid);
        System.out.println("      Output file: " + filePath);
        System.out.println();

        RestClient client = null;
        
        try
        {
            // Create Elasticsearch client
            client = EsClientFactory.createRestClient(esUrl, authPath);

            // Create request
            Request req = new Request("GET", "/" + indexName + "/_search");
            RegistryRequestBuilder bld = new RegistryRequestBuilder();
            String jsonReq = bld.createGetBlobRequest(lidvid);
            req.setJsonEntity(jsonReq);
            
            // Execute request
            Response resp = client.performRequest(req);

            SearchResponseParser respParser = new SearchResponseParser();
            ResponseCB cb = new ResponseCB(lidvid, filePath);
            respParser.parseResponse(resp, cb);
            
            if(!cb.found())
            {
                System.out.println("Could not find a document with lidvid = " + lidvid);
                return;
            }
        }
        catch(ResponseException ex)
        {
            throw new Exception(EsUtils.extractErrorMessage(ex));
        }
        finally
        {
            CloseUtils.close(client);
        }
    }

    
    /**
     * Print help screen
     */
    public void printHelp()
    {
        System.out.println("Usage: registry-manager export-file <options>");

        System.out.println();
        System.out.println("Export a file from blob storage");
        System.out.println();
        System.out.println("Required parameters:");
        System.out.println("  -lidvid <id>    Lidvid of a file to export from blob storage");
        System.out.println("  -file <path>    Output file path");
        System.out.println("Optional parameters:");
        System.out.println("  -auth <file>    Authentication config file");
        System.out.println("  -es <url>       Elasticsearch URL. Default is http://localhost:9200");
        System.out.println("  -index <name>   Elasticsearch index name. Default is 'registry'");
        System.out.println();
    }

}
