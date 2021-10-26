package tt;

import java.io.File;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import org.elasticsearch.client.RestClient;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.mgr.Constants;
import gov.nasa.pds.registry.mgr.dao.SchemaUpdater;
import gov.nasa.pds.registry.mgr.dao.SchemaUpdaterConfig;
import gov.nasa.pds.registry.mgr.dd.LddInfo;
import gov.nasa.pds.registry.mgr.dd.LddLoader;
import gov.nasa.pds.registry.mgr.dd.LddUtils;


public class TestSchemaUpdater
{

    public static void main(String[] args) throws Exception
    {
        testUpdateLdds();
    }
    
    
    public static void testUpdateLdds() throws Exception
    {
        LddLoader lddLoader = new LddLoader();
        lddLoader.loadPds2EsDataTypeMap(new File("src/main/resources/elastic/data-dic-types.cfg"));

        RestClient client = EsClientFactory.createRestClient("localhost", null);
        try
        {
            SchemaUpdaterConfig cfg = new SchemaUpdaterConfig("registry", Constants.DEFAULT_LDD_LIST_URL);
            SchemaUpdater updater = new SchemaUpdater(client, lddLoader, cfg);
            Set<String> namespaces = new TreeSet<>();
            namespaces.add("rings");
            
            boolean updated = updater.updateLdds(namespaces);
            System.out.println(updated);
        }
        finally
        {
            client.close();
        }
    }
    
    
    public static void testLoadLddList() throws Exception
    {
        Map<String, LddInfo> map = LddUtils.loadLddList(new File("src/test/data/ldd_list.csv"));
        map.forEach((ns, info) -> { 
            System.out.println(ns + ", " + info.url + ", " + info.date); 
        });        
    }

    
}
