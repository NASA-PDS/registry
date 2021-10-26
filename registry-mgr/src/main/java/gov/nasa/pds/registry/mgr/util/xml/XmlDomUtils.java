package gov.nasa.pds.registry.mgr.util.xml;

import java.io.File;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.w3c.dom.Document;
import org.w3c.dom.NamedNodeMap;
import org.w3c.dom.Node;
import org.xml.sax.ErrorHandler;


/**
 * Helper methods to work with XML DOM API.
 * 
 * @author karpenko
 */
public class XmlDomUtils
{
    
    /**
     * Read XML from a file into a DOM document.
     * @param dbf document builder factory
     * @param file XML file
     * @return XML DOM model
     * @throws Exception an exception
     */
    public static Document readXml(DocumentBuilderFactory dbf, File file) throws Exception
    {
        DocumentBuilder db = dbf.newDocumentBuilder();
        Document doc = db.parse(file);
        return doc;
    }

    
    /**
     * Read XML from a file into a DOM document.
     * @param file XML file
     * @return XML DOM model
     * @throws Exception an exception
     */
    public static Document readXml(File file) throws Exception
    {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        return readXml(dbf, file);
    }


    /**
     * Read XML from a file into a DOM document.
     * @param xmlFile XML file
     * @param xsdFile XSD schema file to validate XML
     * @param eh custom error handler
     * @return XML DOM model
     * @throws Exception an exception
     */
    public static Document readXml(File xmlFile, File xsdFile, ErrorHandler eh) throws Exception
    {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.setValidating(true);
        dbf.setAttribute("http://java.sun.com/xml/jaxp/properties/schemaLanguage", "http://www.w3.org/2001/XMLSchema");
        dbf.setAttribute("http://java.sun.com/xml/jaxp/properties/schemaSource", xsdFile);

        DocumentBuilder db = dbf.newDocumentBuilder();
        db.setErrorHandler(eh);
        
        return db.parse(xmlFile);
    }


    /**
     * Get node attribute by name.
     * @param node a node
     * @param attributeName attribute name
     * @return an attribute
     */
    public static String getAttribute(Node node, String attributeName)
    {
        if(node == null || node.getAttributes() == null) return null;
        
        Node att = node.getAttributes().getNamedItem(attributeName);
        return att == null ? null : att.getNodeValue();
    }


    /**
     * Get node attributes.
     * @param node a node
     * @return attribute map
     */
    public static NamedNodeMap getAttributes(Node node)
    {
        if(node == null || node.getAttributes() == null) return null;
        return node.getAttributes();
    }

}
