package tt;

import java.io.File;

import gov.nasa.pds.registry.mgr.dao.RegistryRequestBuilder;

public class TestRegistryRequestBld
{

    public static void main(String[] args) throws Exception
    {

    }

    
    private static void testCreateRegistryRequest() throws Exception
    {
        RegistryRequestBuilder bld = new RegistryRequestBuilder(true);

        File schemaFile = new File("/tmp/schema/t2.json");
        String json = bld.createCreateIndexRequest(schemaFile, 3, 1);
        System.out.println(json);
    }
    
    
    private static void testExportDataRequest() throws Exception
    {
        RegistryRequestBuilder bld = new RegistryRequestBuilder(true);
        
        String json = bld.createExportDataRequest("lidvid", "abc123", "lidvid", 100, null);
        System.out.println(json);

        System.out.println();
        json = bld.createExportDataRequest("lidvid", "abc123", "lidvid", 100, "after::123::abc");
        System.out.println(json);

        System.out.println();
        json = bld.createExportAllDataRequest("lidvid", 100, null);
        System.out.println(json);
        
        System.out.println();
        json = bld.createExportAllDataRequest("lidvid", 100, "after::123::abc");
        System.out.println(json);
    }
    
}
