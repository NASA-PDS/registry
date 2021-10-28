package tt;

import org.elasticsearch.client.RestClient;

import gov.nasa.pds.registry.common.es.client.EsClientFactory;


public class TestRestClient
{

    public static void main(String[] args) throws Exception
    {
        RestClient client = EsClientFactory.createRestClient("localhost", null);
        client.close();
    }

}
