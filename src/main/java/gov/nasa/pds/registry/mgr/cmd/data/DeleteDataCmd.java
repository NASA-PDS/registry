package gov.nasa.pds.registry.mgr.cmd.data;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.util.Map;

import org.apache.commons.cli.CommandLine;
import org.elasticsearch.client.Request;
import org.elasticsearch.client.Response;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestClient;

import com.google.gson.Gson;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.common.es.client.EsUtils;
import gov.nasa.pds.registry.mgr.Constants;
import gov.nasa.pds.registry.mgr.cmd.CliCommand;
import gov.nasa.pds.registry.mgr.dao.RegistryRequestBuilder;
import gov.nasa.pds.registry.mgr.util.CloseUtils;


/**
 * A CLI command to delete records from registry index in Elasticsearch.
 * Records can be deleted by LIDVID, LID, PackageID. All records can also be deleted. 
 * 
 * @author karpenko
 */
public class DeleteDataCmd implements CliCommand
{
    private String filterMessage;
    private String regQuery;
    private String refsQuery;

    
    /**
     * Constructor
     */
    public DeleteDataCmd()
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

        buildEsQuery(cmdLine);

        System.out.println("Elasticsearch URL: " + esUrl);
        System.out.println("            Index: " + indexName);
        System.out.println(filterMessage);
        System.out.println();
        
        RestClient client = null;
        
        try
        {
            client = EsClientFactory.createRestClient(esUrl, authPath);
            // Delete from registry index
            deleteByQuery(client, indexName, regQuery);
            // Delete from product references index
            deleteByQuery(client, indexName + "-refs", refsQuery);
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

    
    private static void deleteByQuery(RestClient client, String indexName, String query) throws Exception
    {
        Request req = new Request("POST", "/" + indexName + "/_delete_by_query");
        req.setJsonEntity(query);
        
        Response resp = client.performRequest(req);
        double numDeleted = extractNumDeleted(resp); 
        
        System.out.format("Deleted %.0f document(s) from %s index\n", numDeleted, indexName);
    }
    
    
    @SuppressWarnings("rawtypes")
    private static double extractNumDeleted(Response resp)
    {
        try
        {
            InputStream is = resp.getEntity().getContent();
            Reader rd = new InputStreamReader(is);
            
            Gson gson = new Gson();
            Object obj = gson.fromJson(rd, Object.class);
            rd.close();
            
            obj = ((Map)obj).get("deleted");
            return (Double)obj;
        }
        catch(Exception ex)
        {
            return 0;
        }
    }
    
    
    /**
     * Build Elasticsearch query to delete records.
     * Records can be deleted by LIDVID, LID, PackageID. All records can also be deleted.
     * @param cmdLine
     * @throws Exception
     */
    private void buildEsQuery(CommandLine cmdLine) throws Exception
    {
        // Registry index
        RegistryRequestBuilder regBld = new RegistryRequestBuilder();
        // Product references index
        RegistryRequestBuilder refsBld = new RegistryRequestBuilder();
        
        String id = cmdLine.getOptionValue("lidvid");
        if(id != null)
        {
            this.filterMessage = "           LIDVID: " + id;
            this.regQuery = regBld.createFilterQuery("lidvid", id);
            this.refsQuery = refsBld.createFilterQuery("collection_lidvid", id);
            
            return;
        }
        
        id = cmdLine.getOptionValue("lid");
        if(id != null)
        {
            this.filterMessage = "              LID: " + id;
            this.regQuery = regBld.createFilterQuery("lid", id);
            this.refsQuery = refsBld.createFilterQuery("collection_lid", id);
            
            return;
        }

        id = cmdLine.getOptionValue("packageId");
        if(id != null)
        {
            this.filterMessage = "       Package ID: " + id;
            this.regQuery = regBld.createFilterQuery("_package_id", id);
            this.refsQuery = refsBld.createFilterQuery("_package_id", id);
            
            return;
        }

        if(cmdLine.hasOption("all"))
        {
            this.filterMessage = "Delete all documents ";
            this.regQuery = regBld.createMatchAllQuery();
            this.refsQuery = refsBld.createMatchAllQuery();
            
            return;
        }

        throw new Exception("One of the following options is required: -lidvid, -lid, -packageId, -all");
    }
    
    
    public void printHelp()
    {
        System.out.println("Usage: registry-manager delete-data <options>");

        System.out.println();
        System.out.println("Delete data from registry index");
        System.out.println();
        System.out.println("Required parameters, one of:");
        System.out.println("  -lidvid <id>      Delete data by lidvid");
        System.out.println("  -lid <id>         Delete data by lid");
        System.out.println("  -packageId <id>   Delete data by package id"); 
        System.out.println("  -all              Delete all data");
        System.out.println("Optional parameters:");
        System.out.println("  -auth <file>      Authentication config file");
        System.out.println("  -es <url>         Elasticsearch URL. Default is http://localhost:9200");
        System.out.println("  -index <name>     Elasticsearch index name. Default is 'registry'");
        System.out.println();
    }

}
