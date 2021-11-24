package tt;

import org.apache.logging.log4j.Level;
import org.apache.logging.log4j.core.appender.ConsoleAppender;
import org.apache.logging.log4j.core.config.Configurator;
import org.apache.logging.log4j.core.config.builder.api.AppenderComponentBuilder;
import org.apache.logging.log4j.core.config.builder.api.ConfigurationBuilder;
import org.apache.logging.log4j.core.config.builder.api.ConfigurationBuilderFactory;
import org.apache.logging.log4j.core.config.builder.api.LoggerComponentBuilder;
import org.apache.logging.log4j.core.config.builder.api.RootLoggerComponentBuilder;
import org.apache.logging.log4j.core.config.builder.impl.BuiltConfiguration;

import gov.nasa.pds.registry.common.util.date.PdsDateConverter;


public class TestDateFormats
{
    static PdsDateConverter conv;
    
    public static void main(String[] args) throws Exception
    {
        configureLogger();
        conv = new PdsDateConverter(false);
        
        testPdsDates();
    }

    
    private static void testPdsDates() throws Exception
    {
        testPdsDate("2013-10-24T00:00:00Z");
        testPdsDate("2013-10-24T00:49:37.457Z");
        
        testPdsDate("2013-10-24T01");
        testPdsDate("2013-302T01:02:03.123");
        
        testPdsDate("20130302010203.123");
        
        testPdsDate("2016-09-08Z");
        testPdsDate("2013-03-02");
        testPdsDate("2013-12");
        testPdsDate("2013");
        testPdsDate("2013-001");
        
        testPdsDate("invalid");
    }

    
    private static void testPdsDate(String value) throws Exception
    {
        String solrValue = conv.toIsoInstantString("", value);
        System.out.format("%30s  -->  %s\n", value, solrValue);
    }
    
        
    public static void configureLogger() 
    {
        // Configure Log4j
        ConfigurationBuilder<BuiltConfiguration> cfg = ConfigurationBuilderFactory.newConfigurationBuilder();
        cfg.setStatusLevel(Level.ERROR);
        cfg.setConfigurationName("Test");
        
        // Appenders
        addConsoleAppender(cfg, "console");

        // Root logger
        RootLoggerComponentBuilder rootLog = cfg.newRootLogger(Level.OFF);
        rootLog.add(cfg.newAppenderRef("console"));
        cfg.add(rootLog);
        
        // Default Harvest logger
        LoggerComponentBuilder defLog = cfg.newLogger("gov.nasa.pds", Level.ALL);
        cfg.add(defLog);
        
        // Init Log4j
        Configurator.initialize(cfg.build());
    }

    
    private static void addConsoleAppender(ConfigurationBuilder<BuiltConfiguration> cfg, String name)
    {
        AppenderComponentBuilder appender = cfg.newAppender(name, "CONSOLE");
        appender.addAttribute("target", ConsoleAppender.Target.SYSTEM_OUT);
        appender.add(cfg.newLayout("PatternLayout").addAttribute("pattern", "[%level] %msg%n%throwable"));
        cfg.add(appender);
    }

}
