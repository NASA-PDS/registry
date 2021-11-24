package gov.nasa.pds.api.engineering.serializer;

import gov.nasa.pds.api.model.xml.ProductWithXmlLabel;
import java.io.IOException;
import java.io.OutputStream;

import javax.xml.stream.XMLOutputFactory;
import javax.xml.stream.XMLStreamWriter;

import org.springframework.http.HttpInputMessage;
import org.springframework.http.HttpOutputMessage;
import org.springframework.http.MediaType;
import org.springframework.http.converter.AbstractHttpMessageConverter;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.http.converter.HttpMessageNotWritableException;


public class Pds4XmlProductSerializer extends AbstractHttpMessageConverter<ProductWithXmlLabel> {

		  public Pds4XmlProductSerializer() {
		      super(new MediaType("application", "pds4+xml"));
		  }

		  @Override
		  protected boolean supports(Class<?> clazz) {
		      return ProductWithXmlLabel.class.isAssignableFrom(clazz);
		  }

		  
		  @Override
		  protected ProductWithXmlLabel readInternal(Class<? extends ProductWithXmlLabel> clazz, HttpInputMessage inputMessage)
		          throws IOException, HttpMessageNotReadableException {
		     
		      return new ProductWithXmlLabel();
		  }
		  

		  @Override
		  protected void writeInternal(ProductWithXmlLabel product, HttpOutputMessage outputMessage)
		          throws IOException, HttpMessageNotWritableException {
		      try {
		          OutputStream outputStream = outputMessage.getBody();
		          
		          XMLOutputFactory outputFactory = XMLOutputFactory.newFactory();
		          XMLStreamWriter writer = outputFactory.createXMLStreamWriter(outputStream);
		   
		          String body = product.getLabelXml();
		          
		          outputStream.write(body.getBytes());
		          outputStream.close();
		      } catch (ClassCastException e) {
		    	  this.logger.error("For XML serialization, the Product object must be extended as ProductWithXmlLabel: " + e.getMessage());
		      }
		        catch (Exception e) {
		      }
		  }

	
}

