package gov.nasa.pds.registry.common.util.date;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeFormatterBuilder;
import java.time.format.SignStyle;
import java.time.temporal.ChronoField;
import java.time.temporal.TemporalAccessor;

/**
 * Convert "day of year" dates to ISO instant format.
 * 
 * @author karpenko
 *
 */
public class DoyDateTimeConverter
{
    private DateTimeFormatter DATE_TIME; 
    
    /**
     * Constructor
     */
    public DoyDateTimeConverter()
    {
        DateTimeFormatter LOCAL_DOY = new DateTimeFormatterBuilder()
                .appendValue(ChronoField.YEAR, 4, 10, SignStyle.EXCEEDS_PAD)
                .appendLiteral('-')
                .appendValue(ChronoField.DAY_OF_YEAR, 3)
                .parseStrict()
                .toFormatter();

        DATE_TIME = new DateTimeFormatterBuilder()
                .parseCaseInsensitive()
                // Date
                .append(LOCAL_DOY)
                // Time
                .appendLiteral('T')
                .append(DateConstants.OPTIONAL_TIME)
                // Optional time zone
                .optionalStart()
                .appendZoneRegionId()
                .optionalEnd()
                .toFormatter();
    }


    /**
     * Convert "day of year" dates to ISO instant format.
     * @param value "day of year" date value
     * @return ISO instant
     */
    public Instant toInstant(String value)
    {
        if(value == null) return null;
        
        TemporalAccessor tmp = DATE_TIME.parseBest(value, ZonedDateTime::from, LocalDateTime::from);
        
        if(tmp instanceof ZonedDateTime)
        {
            return ZonedDateTime.from(tmp).toInstant();
        }
        else if(tmp instanceof LocalDateTime)
        {
            return LocalDateTime.from(tmp).toInstant(ZoneOffset.UTC);
        }
        else
        {
            return null;
        }        
    }

}
