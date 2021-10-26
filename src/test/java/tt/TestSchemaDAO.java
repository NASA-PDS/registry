package tt;

import java.time.Instant;
import java.util.Set;
import java.util.TreeSet;

import org.elasticsearch.client.RestClient;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;
import gov.nasa.pds.registry.mgr.dao.DataTypesInfo;
import gov.nasa.pds.registry.mgr.dao.IndexDao;
import gov.nasa.pds.registry.mgr.dao.SchemaDao;
import gov.nasa.pds.registry.mgr.util.Tuple;


public class TestSchemaDAO
{

    public static void main(String[] args) throws Exception
    {
        //testGetLddDate();
        testGetDataTypes();
    }


    private static void testGetLddDate() throws Exception
    {
        RestClient client = EsClientFactory.createRestClient("localhost", null);
        
        SchemaDao dao = new SchemaDao(client);
        Instant date = dao.getLddDate("registry", "test");
        System.out.println(date);
        
        client.close();
    }

    
    private static void testIndexExists() throws Exception
    {
        RestClient client = EsClientFactory.createRestClient("localhost", null);
        IndexDao dao = new IndexDao(client);
        
        boolean b = dao.indexExists("t123");
        System.out.println(b);
        
        client.close();
    }
    
    
    private static void testGetFieldNames() throws Exception
    {
        RestClient client = EsClientFactory.createRestClient("localhost", null);
        SchemaDao dao = new SchemaDao(client);
        
        Set<String> names = dao.getFieldNames("t1");
        for(String name: names)
        {
            System.out.println(name);
        }
        
        client.close();
    }
    
    
    private static void testGetDataTypes() throws Exception
    {
        RestClient client = EsClientFactory.createRestClient("localhost", null);
        
        try
        {
            SchemaDao dao = new SchemaDao(client);
            
            Set<String> ids = new TreeSet<>();
            ids.add("pds:Property_Map/pds:identifier");
            ids.add("abc:test");
            
            DataTypesInfo results = dao.getDataTypes("registry", ids, false);
            
            System.out.println("New fields:");
            for(Tuple res: results.newFields)
            {
                System.out.println("  " + res.item1 + "  -->  " + res.item2);
            }
            
            if(results.lastMissingField != null)
            {
                System.out.println();
                System.out.println("Missing namespaces: " + results.missingNamespaces);
                System.out.println("Last missing field: " + results.lastMissingField);
            }
        }
        finally
        {
            client.close();
        }
    }
}
