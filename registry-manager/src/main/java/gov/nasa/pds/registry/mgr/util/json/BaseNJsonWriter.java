package gov.nasa.pds.registry.mgr.util.json;

import java.io.Closeable;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.StringWriter;

import com.google.gson.stream.JsonWriter;


/**
 * Base abstract class to write data records to a new-line-delimited JSON (NJSON) file.
 * NJSON file has 2 lines per data record: 1 - primary key, 2 - data record.
 * This is the file format used by Elasticsearch bulk load API.  
 * 
 * @author karpenko
 *
 * @param <Record> A data record to write.
 */
public abstract class BaseNJsonWriter<Record> implements Closeable
{
    protected FileWriter writer;
    
    
    /**
     * Constructor
     * @param file output file
     * @throws Exception an exception
     */
    public BaseNJsonWriter(File file) throws Exception
    {
        writer = new FileWriter(file);
    }
    

    /**
     * Overwrite this method to write a data record.
     * @param jw JSON writer
     * @param data a record
     * @throws Exception an exception
     */
    public abstract void writeDataRecord(JsonWriter jw, Record data) throws Exception;

    
    /**
     * Close file.
     */
    @Override
    public void close() throws IOException
    {
        writer.close();
    }
    
    
    /**
     * Write a primary key and a data record.
     * @param pk primary key
     * @param data data record
     * @throws Exception an exception
     */
    public void write(String pk, Record data) throws Exception
    {
        // First line: primary key 
        writePK(pk);
        newLine();
        
        // Second line: data record

        StringWriter sw = new StringWriter();
        JsonWriter jw = new JsonWriter(sw);
        
        jw.beginObject();
        writeDataRecord(jw, data);
        jw.endObject();
        
        jw.close();
        
        writer.write(sw.getBuffer().toString());
        newLine();
    }
    
    
    protected void newLine() throws Exception
    {
        writer.write("\n");
    }


    /**
     * Write primary key
     * @param id primary key
     * @throws Exception an exception
     */
    protected void writePK(String id) throws Exception
    {
        if(id == null) throw new Exception("Primary key is null");
        
        StringWriter sw = new StringWriter();
        JsonWriter jw = new JsonWriter(sw);
        
        jw.beginObject();
        
        jw.name("index");
        jw.beginObject();
        jw.name("_id").value(id);
        jw.endObject();
        
        jw.endObject();
        
        jw.close();
        
        writer.write(sw.getBuffer().toString());
    }
    
}
