package tt;

import java.io.File;
import gov.nasa.pds.registry.mgr.dd.LddLoader;


public class TestLddLoader
{
    
    public static void main(String[] args) throws Exception
    {
        LddLoader loader = new LddLoader();
        loader.loadPds2EsDataTypeMap(new File("src/main/resources/elastic/data-dic-types.cfg"));

        //File ddFile = new File("src/test/data/PDS4_MSN_1B00_1100.JSON");
        //File ddFile = new File("/tmp/schema/PDS4_PDS_JSON_1F00.JSON");
        File ddFile = new File("/tmp/schema/PDS4_IMG_1F00_1810.JSON");        
        File esFile = new File("/tmp/test.dd.json");

        loader.createEsDataFile(ddFile, null, esFile);
        
        System.out.println("Done");
    }

}
