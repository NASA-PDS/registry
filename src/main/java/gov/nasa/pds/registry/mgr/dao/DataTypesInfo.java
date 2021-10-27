package gov.nasa.pds.registry.mgr.dao;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

import gov.nasa.pds.registry.mgr.util.Tuple;


/**
 * This class is used by schema updater.
 * 
 * @author karpenko
 */
public class DataTypesInfo
{
    public List<Tuple> newFields = new ArrayList<>();
    public Set<String> missingNamespaces = new TreeSet<>();
    public String lastMissingField;
}
