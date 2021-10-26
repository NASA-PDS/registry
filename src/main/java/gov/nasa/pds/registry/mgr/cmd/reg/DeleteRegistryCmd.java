package gov.nasa.pds.registry.mgr.cmd.reg;

import org.apache.commons.cli.CommandLine;
import org.elasticsearch.client.Request;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestClient;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.common.es.client.EsUtils;
import gov.nasa.pds.registry.mgr.Constants;
import gov.nasa.pds.registry.mgr.cmd.CliCommand;
import gov.nasa.pds.registry.mgr.dao.IndexDao;
import gov.nasa.pds.registry.mgr.util.CloseUtils;


/**
 * A CLI command to delete registry indices (registry, registry-dd, registry-refs)
 * from Elasticsearch.
 *  
 * @author karpenko
 */
public class DeleteRegistryCmd implements CliCommand
{
    private RestClient client;
    private IndexDao dao;
    
    /**
     * Constructor
     */
    public DeleteRegistryCmd()
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

        System.out.println("Elasticsearch URL: " + esUrl);

        client = EsClientFactory.createRestClient(esUrl, authPath);
        dao = new IndexDao(client);
        
        try
        {
            deleteIndex(indexName);
            deleteIndex(indexName + "-refs");
            deleteIndex(indexName + "-dd");
            System.out.println("Done");            
        }
        finally
        {
            CloseUtils.close(client);
        }
    }

    
    /**
     * Delete Elasticsearch index by name
     * @param indexName Elasticsearch index name
     * @throws Exception
     */
    private void deleteIndex(String indexName) throws Exception
    {
        try
        {
            System.out.println("Deleting index " + indexName);
            
            if(!dao.indexExists(indexName)) 
            {
                return;
            }

            // Create request
            Request req = new Request("DELETE", "/" + indexName);

            // Execute request
            Response resp = client.performRequest(req);
            EsUtils.printWarnings(resp);
        }
        catch(ResponseException ex)
        {
            throw new Exception(EsUtils.extractErrorMessage(ex));
        }
    }
    
    
    /**
     * Print help screen.
     */
    public void printHelp()
    {
        System.out.println("Usage: registry-manager delete-registry <options>");

        System.out.println();
        System.out.println("Delete registry index and all its data");
        System.out.println();
        System.out.println("Optional parameters:");
        System.out.println("  -auth <file>    Authentication config file");
        System.out.println("  -es <url>       Elasticsearch URL. Default is http://localhost:9200");
        System.out.println("  -index <name>   Elasticsearch index name. Default is 'registry'");
    }

}
