package gov.nasa.pds.registry.mgr.cmd.dd;

import java.io.File;

import org.apache.commons.cli.CommandLine;
import org.elasticsearch.client.ResponseException;
import org.elasticsearch.client.RestClient;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.common.es.client.EsUtils;
import gov.nasa.pds.registry.mgr.Constants;
import gov.nasa.pds.registry.mgr.cmd.CliCommand;
import gov.nasa.pds.registry.mgr.dao.SchemaUpdater;
import gov.nasa.pds.registry.mgr.dao.SchemaUpdaterConfig;
import gov.nasa.pds.registry.mgr.dd.LddLoader;
import gov.nasa.pds.registry.mgr.dd.LddUtils;
import gov.nasa.pds.registry.mgr.util.CloseUtils;
import gov.nasa.pds.registry.mgr.util.Logger;

/**
 * A CLI command to update Elasticsearch schema of the "registry" index.
 * NOTE: This command might be removed in future releases. 
 * The same functionality is implemented by "load-data" command.
 * 
 * @author karpenko
 */
public class UpdateSchemaCmd implements CliCommand
{
    /**
     * Constructor
     */
    public UpdateSchemaCmd()
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

        String filePath = cmdLine.getOptionValue("file");
        if(filePath == null) 
        {
            throw new Exception("Missing required parameter '-file'");
        }

        String esUrl = cmdLine.getOptionValue("es", "http://localhost:9200");
        String indexName = cmdLine.getOptionValue("index", Constants.DEFAULT_REGISTRY_INDEX);
        String authPath = cmdLine.getOptionValue("auth");
        String lddCfgUrl = cmdLine.getOptionValue("ldd", Constants.DEFAULT_LDD_LIST_URL);
        
        Logger.info("Elasticsearch URL: " + esUrl);
        Logger.info("Index: " + indexName);

        RestClient client = null;
        
        LddLoader lddLoader = new LddLoader();
        lddLoader.loadPds2EsDataTypeMap(LddUtils.getPds2EsDataTypeCfgFile());
        lddLoader.setElasticInfo(esUrl, indexName, authPath);
        
        try
        {
            client = EsClientFactory.createRestClient(esUrl, authPath);
            SchemaUpdaterConfig suCfg = new SchemaUpdaterConfig(indexName, lddCfgUrl);
            SchemaUpdater su = new SchemaUpdater(client, lddLoader, suCfg);
            su.updateSchema(new File(filePath));
            Logger.info("Done");
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
        System.out.println("Usage: registry-manager update-schema <options>");

        System.out.println();
        System.out.println("Update Elasticsearch schema");
        System.out.println();
        System.out.println("Required parameters:");
        System.out.println("  -file <path>     A file with a list of field names");
        System.out.println("Optional parameters:");
        System.out.println("  -auth <file>     Authentication config file");
        System.out.println("  -es <url>        Elasticsearch URL. Default is http://localhost:9200");
        System.out.println("  -index <name>    Elasticsearch index name. Default is 'registry'");
        System.out.println("  -ldd <url>       PDS LDD configuration url. Default is " + Constants.DEFAULT_LDD_LIST_URL);        
        System.out.println();
    }

}
