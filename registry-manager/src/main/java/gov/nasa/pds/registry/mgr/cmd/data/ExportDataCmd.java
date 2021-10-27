package gov.nasa.pds.registry.mgr.cmd.data;

import java.io.File;

import org.apache.commons.cli.CommandLine;

import gov.nasa.pds.registry.mgr.Constants;
import gov.nasa.pds.registry.mgr.cmd.CliCommand;
import gov.nasa.pds.registry.mgr.dao.RegistryDataExporter;


/**
 * A CLI command to export data from registry index in Elasticsearch.
 * 
 * @author karpenko
 */
public class ExportDataCmd implements CliCommand
{
    private static enum FilterType { LidVid, PackageId, All };
    
    private FilterType filterType;
    private String filterFieldName;
    private String filterFieldValue;
    

    /**
     * Constructor
     */
    public ExportDataCmd()
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
        
        // File path
        String filePath = cmdLine.getOptionValue("file");
        if(filePath == null) 
        {
            throw new Exception("Missing required parameter '-file'");
        }
        
        String esUrl = cmdLine.getOptionValue("es", "http://localhost:9200");
        String indexName = cmdLine.getOptionValue("index", Constants.DEFAULT_REGISTRY_INDEX);
        String authPath = cmdLine.getOptionValue("auth");

        extractFilterParams(cmdLine);
        if(filterType == null)
        {
            throw new Exception("One of the following options is required: -lidvid, -packageId, -all");
        }

        System.out.println("Elasticsearch URL: " + esUrl);
        System.out.println("            Index: " + indexName);
        System.out.println(getFilterMessage());
        System.out.println();
        
        RegistryDataExporter exp = new RegistryDataExporter(esUrl, indexName, authPath);
        exp.setFilterField(filterFieldName, filterFieldValue);
        exp.export(new File(filePath));
    }

    
    /**
     * Extract command-line filter parameters (-lidvid, -packageId, -all)
     * @param cmdLine
     * @throws Exception
     */
    private void extractFilterParams(CommandLine cmdLine) throws Exception
    {
        String id = cmdLine.getOptionValue("lidvid");
        if(id != null)
        {
            filterType = FilterType.LidVid;
            filterFieldName = "lidvid";
            filterFieldValue = id;
            return;
        }
        
        id = cmdLine.getOptionValue("packageId");
        if(id != null)
        {
            filterType = FilterType.PackageId;
            filterFieldName = "_package_id";
            filterFieldValue = id;
            return;            
        }

        if(cmdLine.hasOption("all"))
        {
            filterType = FilterType.All;
            return;
        }
    }
    
    
    /**
     * Get filter message (LIDVID, Package ID, All)
     * @return
     */
    private String getFilterMessage()
    {
        switch(filterType)
        {
        case LidVid:
            return "           LIDVID: " + filterFieldValue;
        case PackageId:
            return "       Package ID: " + filterFieldValue;
        case All:
            return "Export all documents ";
        }
        
        return "";
    }
    
    
    /**
     * Print help screen.
     */
    public void printHelp()
    {
        System.out.println("Usage: registry-manager export-data <options>");

        System.out.println();
        System.out.println("Export data from registry index");
        System.out.println();
        System.out.println("Required parameters:");
        System.out.println("  -file <path>      Output file path");        
        System.out.println("  -lidvid <id>      Export data by lidvid");
        System.out.println("  -packageId <id>   Export data by package id");
        System.out.println("  -all              Export all data");
        System.out.println("Optional parameters:");
        System.out.println("  -auth <file>      Authentication config file");
        System.out.println("  -es <url>         Elasticsearch URL. Default is http://localhost:9200");
        System.out.println("  -index <name>     Elasticsearch index name. Default is 'registry'");
        System.out.println();
    }

    
}
