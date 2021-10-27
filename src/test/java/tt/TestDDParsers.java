package tt;

import java.io.File;

import gov.nasa.pds.registry.mgr.dd.parser.AttributeDictionaryParser;
import gov.nasa.pds.registry.mgr.dd.parser.DDAttribute;


public class TestDDParsers
{
    private static class MyAttrCB implements AttributeDictionaryParser.Callback
    {
        @Override
        public void onAttribute(DDAttribute attr) throws Exception
        {
            System.out.println(attr.id);
        }
    }
    
    
    public static void main(String[] args) throws Exception
    {
        //File file = new File("/tmp/schema/PDS4_PROC_1B00_1100.JSON");
        //File file = new File("/tmp/schema/PDS4_CART_1D00_1933.JSON");
        File file = new File("/tmp/schema/PDS4_PDS_JSON_1E00.JSON");
        
        MyAttrCB cb = new MyAttrCB();
        
        AttributeDictionaryParser parser = new AttributeDictionaryParser(file, cb);
        parser.parse();
    }
}
