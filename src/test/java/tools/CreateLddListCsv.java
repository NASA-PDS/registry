package tools;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;

import com.opencsv.CSVReader;
import com.opencsv.CSVWriter;

import gov.nasa.pds.registry.mgr.dd.LddUtils;
import gov.nasa.pds.registry.mgr.dd.parser.BaseLddParser;
import gov.nasa.pds.registry.mgr.util.file.FileDownloader;


public class CreateLddListCsv
{
    private static final File LDD_DIR = new File("/tmp/schema");
    
    private static class LddInfo
    {
        public String version;
        public String date;
    }
    
    
    public static void main(String[] args) throws Exception
    {
        createLddList();
    }
    
    
    private static void createLddList() throws Exception
    {
        CSVWriter writer = new CSVWriter(new FileWriter("/tmp/schema/ldd_list.csv"));        
        String[] outValues = new String[4];
        
        // Read temporary list file 
        CSVReader reader = new CSVReader(new FileReader("/tmp/schema/ldd_list_tmp.csv"));
        
        String[] inValues;
        int lineNum = 0;
        while((inValues = reader.readNext()) != null)
        {
            lineNum++;
            if(inValues.length < 2)
            {
                System.out.println("[WARN] Line " + lineNum + ": Invalid record.");
                continue;
            }
            
            String namespace = inValues[0];
            
            String url = inValues[1];
            LddInfo lddInfo = getLddInfo(url);
            
            outValues[0] = namespace;
            outValues[1] = url;
            outValues[2] = lddInfo.version;
            outValues[3] = LddUtils.lddDateToIsoInstant(lddInfo.date);
            
            writer.writeNext(outValues, true);
        }

        writer.close();
        reader.close();
    }

    
    private static LddInfo getLddInfo(String url) throws Exception
    {
        String fileName = getFileNameFromUrl(url);
        File filePath = new File(LDD_DIR, fileName);
        
        // Download LDD if the file doesn't exist
        if(!filePath.exists())
        {
            FileDownloader fdlr = new FileDownloader();
            fdlr.download(url, filePath);
        }
        
        // Parse LDD to extract version and date
        BaseLddParser parser = new BaseLddParser(filePath);
        parser.parse();
        
        LddInfo info = new LddInfo();
        info.version = parser.getLddVersion();
        info.date = parser.getLddDate();
        
        if(info.version == null) throw new Exception("Missing LDD version: " + url);
        if(info.date == null) throw new Exception("Missing LDD date: " + url);
                
        return info;
    }
    
    
    private static String getFileNameFromUrl(String url)
    {
        if(url == null) return null;
        
        int idx = url.lastIndexOf('/');
        if(idx < 0) return url;
        
        return url.substring(idx+1);
    }
}
