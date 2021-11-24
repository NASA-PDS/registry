package gov.nasa.pds.registry.mgr.util.xml;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathExpression;
import javax.xml.xpath.XPathFactory;

import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;


/**
 * Helper methods to work with XPath API.
 * 
 * @author karpenko
 */
public class XPathUtils
{
    private XPathFactory xpf;
    
    /**
     * Constructor
     */
    public XPathUtils()
    {
        xpf = XPathFactory.newInstance();
    }
    
    
    /**
     * Compile XPath
     * @param xpf XPath factory
     * @param str String XPath to compile
     * @return compiled XPath
     * @throws Exception an exception
     */
    public static XPathExpression compileXPath(XPathFactory xpf, String str) throws Exception
    {
        XPath xpath = xpf.newXPath();
        XPathExpression expr = xpath.compile(str);
        return expr;
    }

    
    /**
     * Get a String value of an XPath 
     * @param doc XML DOM model
     * @param expr an XPath
     * @return a string value
     * @throws Exception an exception
     */
    public static String getStringValue(Document doc, XPathExpression expr) throws Exception
    {
        Object res = expr.evaluate(doc, XPathConstants.STRING);
        return (res == null) ? null : res.toString();
    }

    
    /**
     * Get a list of String values of an XPath
     * @param obj parent node
     * @param expr an XPath
     * @return String list
     * @throws Exception an exception
     */
    public static List<String> getStringList(Object obj, XPathExpression expr) throws Exception
    {
        String[] values = getStringArray(obj, expr);
        return values == null ? null : Arrays.asList(values);
    }

    
    /**
     * Get a list of String values of an XPath
     * @param obj parent node
     * @param xpath an XPath
     * @return String list
     * @throws Exception an exception
     */
    public List<String> getStringList(Object obj, String xpath) throws Exception
    {
        XPathExpression expr = compileXPath(xpf, xpath);
        return getStringList(obj, expr);
    }

    
    /**
     * Get a set of String values of an XPath
     * @param doc XML DOM model
     * @param xpath an XPath
     * @return String set
     * @throws Exception an exception
     */
    public Set<String> getStringSet(Document doc, String xpath) throws Exception
    {
        XPathExpression expr = compileXPath(xpf, xpath);
        List<String> list = getStringList(doc, expr);
        
        if(list == null || list.size() == 0) return null;

        Set<String> set = new HashSet<>();
        set.addAll(list);
        return set;
    }

    
    /**
     * Get an array of String values of an XPath
     * @param obj parent node
     * @param expr an XPath
     * @return String array
     * @throws Exception an exception
     */
    public static String[] getStringArray(Object obj, XPathExpression expr) throws Exception
    {
        NodeList nodes = (NodeList) expr.evaluate(obj, XPathConstants.NODESET);
        if (nodes == null || nodes.getLength() == 0)
            return null;

        String vals[] = new String[nodes.getLength()];
        for (int i = 0; i < nodes.getLength(); i++)
        {
            vals[i] = nodes.item(i).getTextContent();
        }

        return vals;
    }

    
    /**
     * Get node list of an XPath
     * @param item parent node
     * @param expr an XPath
     * @return node list
     * @throws Exception an exception
     */
    public static NodeList getNodeList(Object item, XPathExpression expr) throws Exception
    {
        if(item == null) return null;
        
        NodeList nodes = (NodeList)expr.evaluate(item, XPathConstants.NODESET);
        return nodes;
    }
    
    
    /**
     * Get node list of an XPath
     * @param item parent node
     * @param xpath an XPath
     * @return node list
     * @throws Exception an exception
     */
    public NodeList getNodeList(Object item, String xpath) throws Exception
    {
        if(item == null) return null;
        XPathExpression xpe = compileXPath(xpf, xpath);

        return getNodeList(item, xpe);
    }

    
    /**
     * Get node count of an XPath
     * @param item parent node
     * @param xpath an XPath
     * @return node count
     * @throws Exception an exception
     */
    public int getNodeCount(Object item, String xpath) throws Exception
    {
        if(item == null) return 0;
        XPathExpression xpe = compileXPath(xpf, xpath);

        NodeList nodes = getNodeList(item, xpe);
        return nodes == null ? 0 : nodes.getLength();
    }
    
    
    /**
     * Get first node of an XPath
     * @param item parent node
     * @param xpath an XPath
     * @return a node
     * @throws Exception an exception
     */
    public Node getFirstNode(Object item, String xpath) throws Exception
    {
        if(item == null) return null;
        
        XPathExpression xpe = XPathUtils.compileXPath(xpf, xpath);
        NodeList nodes = XPathUtils.getNodeList(item, xpe);
        
        if(nodes == null || nodes.getLength() == 0) 
        {
            return null;
        }
        else
        {
            return nodes.item(0);
        }
    }
    
}
