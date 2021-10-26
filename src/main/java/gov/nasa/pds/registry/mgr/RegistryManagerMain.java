package gov.nasa.pds.registry.mgr;

import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Registry manager main class.
 *  
 * @author karpenko
 */
public class RegistryManagerMain
{
    public static void main(String[] args)
    {
        // We don't use "java.util" logger.
        Logger log = Logger.getLogger("");
        log.setLevel(Level.OFF);
        
        RegistryManagerCli cli = new RegistryManagerCli();
        cli.run(args);
    }

}
