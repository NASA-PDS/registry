package tools;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;

import com.google.gson.Gson;

public class MigrateDD
{
    private static class DDItem
    {
        public String es_field_name;
        public String es_data_type;
        
        public String class_ns;
        public String class_name;
        
        public String attr_ns;
        public String attr_name;
        
        public String data_type;
        public String description;
    }

    
    private static class Index
    {
        public String _id;
    }
    
    
    private static class IDItem
    {
        public Index index;
    }
    
    
    public static void main(String[] args) throws Exception
    {
        Gson gson = new Gson();
        
        File fileIn = new File("/tmp/dd.json");
        File fileOut = new File("/tmp/dd.json.new");
        
        BufferedReader rd = new BufferedReader(new FileReader(fileIn));
        FileWriter wr = new FileWriter(fileOut, StandardCharsets.UTF_8);

        while(true)
        {
            String line1 = rd.readLine();
            if(line1 == null) break;
            String line2 = rd.readLine();
            if(line2 == null) break;

            // Parse ID
            IDItem idItem = gson.fromJson(line1, IDItem.class);
            String[] tokens = idItem.index._id.split("/");
            if(tokens.length == 4)
            {
                idItem.index._id = tokens[0] + ":" + tokens[1] + "/" + tokens[2] + ":" + tokens[3];
            }
            
            // Write new record
            String newJson = gson.toJson(idItem);
            wr.write(newJson);
            wr.write("\n");

            // Parse data
            DDItem item = gson.fromJson(line2, DDItem.class);

            // Convert field name
            tokens = item.es_field_name.split("/");
            if(tokens.length == 4)
            {
                item.es_field_name = tokens[0] + ":" + tokens[1] + "/" + tokens[2] + ":" + tokens[3];
                if(item.class_ns == null) item.class_ns = tokens[0];
                if(item.class_name == null) item.class_name = tokens[1];
                if(item.attr_ns == null) item.attr_ns = tokens[2];
                if(item.attr_name == null) item.attr_name = tokens[3];
            }
            
            // Write new record
            newJson = gson.toJson(item);
            wr.write(newJson);
            wr.write("\n");
        }
        
        wr.close();
        rd.close();
    }

}
