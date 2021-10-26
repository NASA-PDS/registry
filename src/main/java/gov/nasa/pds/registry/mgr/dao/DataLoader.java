package gov.nasa.pds.registry.mgr.dao;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.UnknownHostException;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

import com.google.gson.Gson;

import gov.nasa.pds.registry.common.es.client.EsUtils;
import gov.nasa.pds.registry.common.es.client.HttpConnectionFactory;
import gov.nasa.pds.registry.mgr.util.CloseUtils;
import gov.nasa.pds.registry.mgr.util.Logger;


/**
 * Loads data from an NJSON (new-line-delimited JSON) file into Elasticsearch.
 * NJSON file has 2 lines per record: 1 - primary key, 2 - data record.
 * This is the standard file format used by Elasticsearch bulk load API.
 * Data are loaded in batches.
 * 
 * @author karpenko
 */
public class DataLoader
{
    private int printProgressSize = 5000;
    
    private int batchSize = 100;
    private HttpConnectionFactory conFactory; 
    private int totalRecords;


    /**
     * Constructor
     * @param esUrl Elasticsearch URL, e.g., "http://localhost:9200"
     * @param indexName Elasticsearch index name
     * @param authConfigFile Elasticsearch authentication configuration file 
     * (see Registry Manager documentation for more info)
     * @throws Exception an exception
     */
    public DataLoader(String esUrl, String indexName, String authConfigFile) throws Exception
    {
        conFactory = new HttpConnectionFactory(esUrl, indexName, "_bulk");
        conFactory.initAuth(authConfigFile);
    }
    
    
    /**
     * Set data batch size
     * @param size batch size
     */
    public void setBatchSize(int size)
    {
        if(size <= 0) throw new IllegalArgumentException("Batch size should be > 0");
        this.batchSize = size;
    }

    
    /**
     * Load data from an NJSON (new-line-delimited JSON) file into Elasticsearch.
     * @param file NJSON (new-line-delimited JSON) file to load
     * @throws Exception an exception
     */
    public void loadFile(File file) throws Exception
    {
        Logger.info("Loading ES data file: " + file.getAbsolutePath());
        
        BufferedReader rd = new BufferedReader(new FileReader(file));
        loadData(rd);
    }
    
    
    /**
     * Load data from a zipped NJSON (new-line-delimited JSON) file into Elasticsearch.
     * @param zipFile Zip file with an NJSON data file.
     * @param fileName NJSON data file name in the Zip file.
     * @throws Exception an exception
     */
    public void loadZippedFile(File zipFile, String fileName) throws Exception
    {
        Logger.info("Loading ES data file: " + zipFile.getAbsolutePath() + ":" + fileName);
        
        ZipFile zip = new ZipFile(zipFile);
        
        try
        {
            ZipEntry ze = zip.getEntry(fileName);
            if(ze == null) 
            {
                throw new Exception("Could not find " + fileName +  " in " + zipFile.getAbsolutePath());
            }
            
            BufferedReader rd = new BufferedReader(new InputStreamReader(zip.getInputStream(ze)));
            loadData(rd);
        }
        finally
        {
            CloseUtils.close(zip);
        }
    }
    
    
    /**
     * Load NJSON data from a reader.
     * @param rd reader
     * @throws Exception an exception
     */
    private void loadData(BufferedReader rd) throws Exception
    {
        totalRecords = 0;
        
        try
        {
            String firstLine = rd.readLine();
            // File is empty
            if(firstLine == null || firstLine.isEmpty()) return;
            
            while((firstLine = loadBatch(rd, firstLine)) != null)
            {
                if(totalRecords % printProgressSize == 0)
                {
                    Logger.info("Loaded " + totalRecords + " document(s)");
                }
            }
            
            Logger.info("Loaded " + totalRecords + " document(s)");
        }
        finally
        {
            CloseUtils.close(rd);
        }
    }

    
    /**
     * Load next batch of NJSON (new-line-delimited JSON) data.
     * @param fileReader Reader object with NJSON data.
     * @param firstLine NJSON file has 2 lines per record: 1 - primary key, 2 - data record.
     * This is the primary key line.
     * @return First line of 2-line NJSON record (line 1: primary key, line 2: data)
     * @throws Exception an exception
     */
    private String loadBatch(BufferedReader fileReader, String firstLine) throws Exception
    {
        HttpURLConnection con = null;
        
        try
        {
            con = conFactory.createConnection();
            con.setDoInput(true);
            con.setDoOutput(true);
            con.setRequestMethod("POST");
            con.setRequestProperty("content-type", "application/x-ndjson; charset=utf-8");
            
            OutputStreamWriter writer = new OutputStreamWriter(con.getOutputStream(), "UTF-8");
            
            // First record
            String line1 = firstLine;
            String line2 = fileReader.readLine();
            if(line2 == null) throw new Exception("Premature end of file");
            
            writer.write(line1);
            writer.write("\n");
            writer.write(line2);
            writer.write("\n");
            
            int numRecords = 1;
            while(numRecords < batchSize)
            {
                line1 = fileReader.readLine();
                if(line1 == null) break;
                
                line2 = fileReader.readLine();
                if(line2 == null) throw new Exception("Premature end of file");
                
                writer.write(line1);
                writer.write("\n");
                writer.write(line2);
                writer.write("\n");
                
                numRecords++;
            }
            
            if(numRecords == batchSize)
            {
                // Let's find out if there are more records
                line1 = fileReader.readLine();
                if(line1 != null && line1.isEmpty()) line1 = null;
            }
            
            writer.flush();
            writer.close();
        
            // Check for Elasticsearch errors.
            String respJson = getLastLine(con.getInputStream());
            Logger.debug(respJson);
            
            if(responseHasErrors(respJson))
            {
                throw new Exception("Could not load data.");
            }
            
            totalRecords += numRecords;

            return line1;
        }
        catch(UnknownHostException ex)
        {
            throw new Exception("Unknown host " + conFactory.getHostName());
        }
        catch(IOException ex)
        {
            // Get HTTP response code
            int respCode = getResponseCode(con);
            if(respCode <= 0) throw ex;
            
            // Try extracting JSON from multi-line error response (last line) 
            String json = getLastLine(con.getErrorStream());
            if(json == null) throw ex;
            
            // Parse error JSON to extract reason.
            String msg = EsUtils.extractReasonFromJson(json);
            if(msg == null) msg = json;
            
            throw new Exception(msg);
        }
    }
    
    
    @SuppressWarnings({ "rawtypes", "unchecked" })
    private boolean responseHasErrors(String resp)
    {
        try
        {
            // Parse JSON response
            Gson gson = new Gson();
            Map json = (Map)gson.fromJson(resp, Object.class);
            
            Boolean hasErrors = (Boolean)json.get("errors");
            if(hasErrors)
            {
                List<Object> list = (List)json.get("items");
                
                // List size = batch size (one item per document)
                // NOTE: Only few items in the list could have errors
                for(Object item: list)
                {
                    Map index = (Map)((Map)item).get("index");
                    Map error = (Map)index.get("error");
                    if(error != null)
                    {
                        String message = (String)error.get("reason");
                        Logger.error(message);
                        return true;
                    }
                }
            }

            return false;
        }
        catch(Exception ex)
        {
            return false;
        }
    }
    
    
    /**
     * Get HTTP response code, e.g., 200 (OK)
     * @param con HTTP connection
     * @return HTTP response code, e.g., 200 (OK)
     */
    private static int getResponseCode(HttpURLConnection con)
    {
        if(con == null) return -1;
        
        try
        {
            return con.getResponseCode();
        }
        catch(Exception ex)
        {
            return -1;
        }
    }

    
    /**
     * This method is used to parse multi-line Elasticsearch error responses.
     * JSON error response is on the last line of a message.
     * @param is input stream
     * @return Last line
     */
    private static String getLastLine(InputStream is)
    {
        String lastLine = null;

        try
        {
            BufferedReader rd = new BufferedReader(new InputStreamReader(is));

            String line;
            while((line = rd.readLine()) != null)
            {
                lastLine = line;
            }
        }
        catch(Exception ex)
        {
            // Ignore
        }
        finally
        {
            CloseUtils.close(is);
        }
        
        return lastLine;
    }
}
