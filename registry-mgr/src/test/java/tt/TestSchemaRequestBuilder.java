package tt;

import gov.nasa.pds.registry.mgr.dao.SchemaRequestBuilder;

public class TestSchemaRequestBuilder
{
    public static void main(String[] args) throws Exception
    {
        testGetLddInfoRequest();
    }
    
    
    public static void testGetLddInfoRequest() throws Exception
    {
        SchemaRequestBuilder bld = new SchemaRequestBuilder(true);
        String req = bld.createGetLddInfoRequest("pds");
        System.out.println(req);
    }
}
