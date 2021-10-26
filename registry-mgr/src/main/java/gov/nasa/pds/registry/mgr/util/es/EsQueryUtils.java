package gov.nasa.pds.registry.mgr.util.es;

import java.io.IOException;

import com.google.gson.stream.JsonWriter;

/**
 * Helper methods for building Elasticsearch queries. 
 *  
 * @author karpenko
 */
public class EsQueryUtils
{
    /**
     * Append "match_all" object.
     * @param writer JSON writer
     * @throws IOException an exception
     */
    public static void appendMatchAll(JsonWriter writer) throws IOException
    {
        writer.name("match_all");
        writer.beginObject();
        writer.endObject();
    }


    /**
     * Append match all query.
     * @param writer JSON writer
     * @throws IOException an exception
     */
    public static void appendMatchAllQuery(JsonWriter writer) throws IOException
    {
        writer.name("query");
        writer.beginObject();
        appendMatchAll(writer);
        writer.endObject();
    }

    
    /**
     * Append filter query
     * @param writer JSON writer
     * @param field field name
     * @param value field value
     * @throws IOException an exception
     */
    public static void appendFilterQuery(JsonWriter writer, String field, String value) throws IOException
    {
        writer.name("query");
        writer.beginObject();

        writer.name("bool");
        writer.beginObject();
        appendMustMatchAll(writer);
        appendTermFilter(writer, field, value);
        writer.endObject();

        writer.endObject();
    }
    
    
    /**
     * Append must match all criterion
     * @param writer JSON writer
     * @throws IOException an exception
     */
    private static void appendMustMatchAll(JsonWriter writer) throws IOException
    {
        writer.name("must");
        writer.beginObject();
        appendMatchAll(writer);
        writer.endObject();
    }

    
    /**
     * Append term filter
     * @param writer JSON writer
     * @param field field name
     * @param value field value
     * @throws IOException an exception
     */
    private static void appendTermFilter(JsonWriter writer, String field, String value) throws IOException
    {
        writer.name("filter");
        writer.beginObject();

        writer.name("term");
        writer.beginObject();
        writer.name(field).value(value);
        writer.endObject();

        writer.endObject();
    }

}
