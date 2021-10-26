package gov.nasa.pds.registry.mgr;

import java.util.HashMap;
import java.util.Map;
import java.util.jar.Attributes;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;

import gov.nasa.pds.registry.mgr.cmd.CliCommand;
import gov.nasa.pds.registry.mgr.cmd.data.DeleteDataCmd;
import gov.nasa.pds.registry.mgr.cmd.data.ExportDataCmd;
import gov.nasa.pds.registry.mgr.cmd.data.ExportFileCmd;
import gov.nasa.pds.registry.mgr.cmd.data.LoadDataCmd;
import gov.nasa.pds.registry.mgr.cmd.data.SetArchiveStatusCmd;
import gov.nasa.pds.registry.mgr.cmd.dd.DeleteDDCmd;
import gov.nasa.pds.registry.mgr.cmd.dd.ExportDDCmd;
import gov.nasa.pds.registry.mgr.cmd.dd.LoadDDCmd;
import gov.nasa.pds.registry.mgr.cmd.dd.UpdateSchemaCmd;
import gov.nasa.pds.registry.mgr.cmd.reg.CreateRegistryCmd;
import gov.nasa.pds.registry.mgr.cmd.reg.DeleteRegistryCmd;
import gov.nasa.pds.registry.mgr.util.ExceptionUtils;
import gov.nasa.pds.registry.mgr.util.Logger;
import gov.nasa.pds.registry.mgr.util.ManifestUtils;

/**
 * Main CLI (Command-Line Interface) manager / dispatcher.
 * RegistryManagerCli.run() method parses command-line parameters and 
 * calls different CLI commands, such as "load-data", "create-registry", etc.
 *   
 * @author karpenko
 */
public class RegistryManagerCli
{
    private Map<String, CliCommand> commands;
    private CliCommand command;
    private Options options;
    private CommandLine cmdLine;
    
    
    /**
     * Constructor
     */
    public RegistryManagerCli()
    {
        initCommands();
        initOptions();
    }
    
    
    /**
     * Print main help screen.
     */
    public static void printHelp()
    {
        System.out.println("Usage: registry-manager <command> <options>");

        System.out.println();
        System.out.println("Commands:");
        
        System.out.println();
        System.out.println("Data:");
        System.out.println("  load-data            Load data into registry index");
        System.out.println("  delete-data          Delete data from registry index");
        System.out.println("  export-data          Export data from registry index");
        System.out.println("  export-file          Export a file from blob storage");
        System.out.println("  set-archive-status   Set product archive status");
        
        System.out.println();
        System.out.println("Registry:");
        System.out.println("  create-registry      Create registry and data dictionary indices");
        System.out.println("  delete-registry      Delete registry and data dictionary indices and all its data");        
        
        System.out.println();
        System.out.println("Data Dictionary:");
        System.out.println("  load-dd              Load data into data dictionary");
        System.out.println("  delete-dd            Delete data from data dictionary");        
        System.out.println("  export-dd            Export data dictionary");
        System.out.println("  update-schema        Update registry schema");

        System.out.println();
        System.out.println("Other:");
        System.out.println("  -V, --version        Print Registry Manager version");

        System.out.println();
        System.out.println("Options:");
        System.out.println("  -help        Print help for a command");
        System.out.println("  -v <value>   Log verbosity: DEBUG, INFO, WARN, ERROR. Default is INFO.");
        
        System.out.println();
        System.out.println("Pass -help after any command to see command-specific usage information, for example,");
        System.out.println("  registry-manager load-data -help");
    }

    
    /**
     * Print Registry Manager version
     */
    public static void printVersion()
    {
        String version = RegistryManagerCli.class.getPackage().getImplementationVersion();
        System.out.println("Registry Manager version: " + version);
        Attributes attrs = ManifestUtils.getAttributes();
        if(attrs != null)
        {
            System.out.println("Build time: " + attrs.getValue("Build-Time"));
        }
    }


    /**
     * Main entry point into this class. 
     * @param args Command line arguments from main() function.
     */
    public void run(String[] args)
    {
        // Print help if there are no command line parameters
        if(args.length == 0)
        {
            printHelp();
            System.exit(0);
        }

        // Version
        if(args.length == 1 && ("-V".equals(args[0]) || "--version".equals(args[0])))
        {
            printVersion();
            System.exit(0);
        }        
        
        // Parse command line arguments
        if(!parse(args))
        {
            System.out.println();
            printHelp();
            System.exit(1);
        }

        initLogger();
        
        // Run command
        if(!runCommand())
        {
            System.exit(1);
        }        
    }

    
    private void initLogger()
    {
        String verbosity = cmdLine.getOptionValue("v", "INFO");
        int level = parseLogLevel(verbosity);
        Logger.setLevel(level);
    }
    

    private static int parseLogLevel(String verbosity)
    {
        // Logger is not setup yet. Print to console.
        if(verbosity == null)
        {
            System.out.println("[WARN] Log verbosity is not set. Will use 'INFO'.");
            return Logger.LEVEL_INFO;
        }
        
        switch(verbosity.toUpperCase())
        {
        case "DEBUG": return Logger.LEVEL_DEBUG;
        case "INFO": return Logger.LEVEL_INFO;
        case "WARN": return Logger.LEVEL_WARN;
        case "ERROR": return Logger.LEVEL_ERROR;
        }

        // Logger is not setup yet. Print to console.
        System.out.println("[WARN] Invalid log verbosity '" + verbosity + "'. Will use 'INFO'.");
        return Logger.LEVEL_INFO;
    }
    
    
    private boolean runCommand()
    {
        try
        {
            command.run(cmdLine);
        }
        catch(Exception ex)
        {
            Logger.error(ExceptionUtils.getMessage(ex));
            return false;
        }
        
        return true;
    }
    
    
    /**
     * Parse command line parameters. Apache Commons CLI library is used.
     * @param pArgs
     * @return
     */
    private boolean parse(String[] pArgs)
    {
        try
        {
            CommandLineParser parser = new DefaultParser();
            cmdLine = parser.parse(options, pArgs);
            
            String[] args = cmdLine.getArgs();
            if(args == null || args.length == 0)
            {
                Logger.error("Missing command.");
                return false;
            }

            if(args.length > 1)
            {
                Logger.error("Invalid command: " + String.join(" ", args)); 
                return false;
            }
            
            this.command = commands.get(args[0]);
            if(this.command == null)
            {
                Logger.error("Invalid command: " + args[0]);
                return false;
            }
            
            return true;
        }
        catch(ParseException ex)
        {
            System.out.println("[ERROR] " + ex.getMessage());
            return false;
        }
    }

    
    /**
     * Initialize all CLI commands
     */
    private void initCommands()
    {
        commands = new HashMap<>();

        // Registry
        commands.put("create-registry", new CreateRegistryCmd());
        commands.put("delete-registry", new DeleteRegistryCmd());

        // Data dictionary
        commands.put("load-dd", new LoadDDCmd());
        commands.put("delete-dd", new DeleteDDCmd());
        commands.put("export-dd", new ExportDDCmd());
        commands.put("update-schema", new UpdateSchemaCmd());
        
        // Data
        commands.put("load-data", new LoadDataCmd());
        commands.put("delete-data", new DeleteDataCmd());
        commands.put("export-data", new ExportDataCmd());
        commands.put("export-file", new ExportFileCmd());
        commands.put("set-archive-status", new SetArchiveStatusCmd());
    }
    
    
    /**
     * Initialize Apache Commons CLI library.
     */
    private void initOptions()
    {
        options = new Options();
        
        Option.Builder bld;
        
        bld = Option.builder("help");
        options.addOption(bld.build());
        
        bld = Option.builder("es").hasArg().argName("url");
        options.addOption(bld.build());

        bld = Option.builder("auth").hasArg().argName("file");
        options.addOption(bld.build());

        bld = Option.builder("file").hasArg().argName("path");
        options.addOption(bld.build());

        bld = Option.builder("dir").hasArg().argName("path");
        options.addOption(bld.build());

        // Data dictionary commands
        bld = Option.builder("id").hasArg().argName("id");
        options.addOption(bld.build());

        bld = Option.builder("ns").hasArg().argName("namespace");
        options.addOption(bld.build());
        
        bld = Option.builder("dd").hasArg().argName("path");
        options.addOption(bld.build());

        bld = Option.builder("dump").hasArg().argName("path");
        options.addOption(bld.build());

        bld = Option.builder("csv").hasArg().argName("path");
        options.addOption(bld.build());

        bld = Option.builder("updateSchema").hasArg().argName("y/n");
        options.addOption(bld.build());

        bld = Option.builder("ldd").hasArg().argName("url");
        options.addOption(bld.build());

        // Data commands
        bld = Option.builder("lidvid").hasArg().argName("id");
        options.addOption(bld.build());

        bld = Option.builder("lid").hasArg().argName("id");
        options.addOption(bld.build());

        bld = Option.builder("packageId").hasArg().argName("id");
        options.addOption(bld.build());
        
        bld = Option.builder("all");
        options.addOption(bld.build());
        
        bld = Option.builder("status").hasArg().argName("status");
        options.addOption(bld.build());
        
        // Registry
        bld = Option.builder("index").hasArg().argName("name");
        options.addOption(bld.build());

        bld = Option.builder("schema").hasArg().argName("path");
        options.addOption(bld.build());

        bld = Option.builder("shards").hasArg().argName("#");
        options.addOption(bld.build());

        bld = Option.builder("replicas").hasArg().argName("#");
        options.addOption(bld.build());
        
        // Logger
        bld = Option.builder("log").hasArg().argName("file");
        options.addOption(bld.build());
        
        bld = Option.builder("v").hasArg().argName("level");
        options.addOption(bld.build());
    }
    
}

