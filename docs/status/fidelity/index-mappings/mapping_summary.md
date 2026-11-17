# Index mapping audit

Run time: 2026-11-16

- Indices read: **20**
- Discrepancies: **182** (28 errors, 154 warnings)
- A field defined on at least 80% of a group's indices is expected on all of them
- Possibly stale or test indices (not compared): **1**

## Possibly stale or test indices

These indices are not named after a tenant node (`<node>-registry`), so they were left out of the
comparison. They may be stale copies or test data and are candidates for cleanup. Confirm with their
owner before deleting; the audit never changes or deletes anything.

| Index | Documents | Mapped fields | Refs index |
|---|---|---|---|
| edunn-geo-registry | 5,239,034 | 2 | no |

## Per index

| Group | Index | Fields | dynamic | Missing (error) | Missing (warning) | Type mismatches |
|---|---|---|---|---|---|---|
| registry | en-registry | 565 | false | 0 | 10 | 2 |
| registry | geo-registry | 1287 | false | 0 | 0 | 2 |
| registry | img-registry | 1051 | false | 0 | 22 | 1 |
| registry | naif-registry | 134 | false | 0 | 97 | 10 |
| registry | ppi-registry | 403 | false | 0 | 2 | 0 |
| registry | psa-registry | 985 | false | 0 | 6 | 0 |
| registry | rms-registry | 591 | false | 0 | 12 | 1 |
| registry | sbnpsi-registry | 1356 | false | 0 | 0 | 0 |
| registry | sbnumd-registry | 939 | false | 0 | 3 | 9 |
| registry | temp-atm-registry | 765 | false | 2 | 2 | 1 |
| registry-refs | en-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | geo-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | img-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | naif-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | ppi-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | psa-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | rms-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | sbnpsi-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | sbnumd-registry-refs | 10 | false | 0 | 0 | 0 |
| registry-refs | atm-registry-refs | 10 | false | 0 | 0 | 0 |

## Fields missing from some indices

| Severity | Group | Field | Expected type | Missing from |
|---|---|---|---|---|
| error | registry | `ops:Provenance/ops:superseded_by` | keyword | temp-atm-registry |
| error | registry | `vid` | float | temp-atm-registry |
| warning | registry | `disp:Display_Direction/disp:horizontal_display_axis` | keyword | naif-registry |
| warning | registry | `disp:Display_Direction/disp:horizontal_display_direction` | keyword | naif-registry |
| warning | registry | `disp:Display_Direction/disp:vertical_display_axis` | keyword | naif-registry |
| warning | registry | `disp:Display_Direction/disp:vertical_display_direction` | keyword | naif-registry |
| warning | registry | `geom:SPICE_Kernel_Identification/geom:spice_kernel_file_name` | keyword | naif-registry, ppi-registry |
| warning | registry | `pds:Affiliation/pds:organization_name` | keyword | naif-registry, psa-registry |
| warning | registry | `pds:Alias/pds:alternate_id` | keyword | naif-registry, rms-registry |
| warning | registry | `pds:Array_2D_Image/pds:axes` | long | naif-registry |
| warning | registry | `pds:Array_2D_Image/pds:axis_index_order` | keyword | naif-registry |
| warning | registry | `pds:Array_2D_Image/pds:local_identifier` | keyword | naif-registry |
| warning | registry | `pds:Array_2D_Image/pds:offset` | long | naif-registry |
| warning | registry | `pds:Array_3D_Image/pds:axes` | long | naif-registry, rms-registry |
| warning | registry | `pds:Array_3D_Image/pds:axis_index_order` | keyword | naif-registry, rms-registry |
| warning | registry | `pds:Array_3D_Image/pds:description` | text | naif-registry, rms-registry |
| warning | registry | `pds:Array_3D_Image/pds:local_identifier` | keyword | naif-registry, rms-registry |
| warning | registry | `pds:Array_3D_Image/pds:offset` | long | naif-registry, rms-registry |
| warning | registry | `pds:Axis_Array/pds:axis_name` | keyword | naif-registry |
| warning | registry | `pds:Axis_Array/pds:elements` | long | naif-registry |
| warning | registry | `pds:Axis_Array/pds:sequence_number` | long | naif-registry |
| warning | registry | `pds:Bundle/pds:description` | text | sbnumd-registry |
| warning | registry | `pds:Bundle_Member_Entry/pds:lid_reference` | keyword | naif-registry |
| warning | registry | `pds:Bundle_Member_Entry/pds:lidvid_reference` | keyword | img-registry |
| warning | registry | `pds:Citation_Information/pds:editor_list` | text | naif-registry |
| warning | registry | `pds:Collection/pds:description` | text | en-registry, img-registry |
| warning | registry | `pds:Context_Area/pds:comment` | text | naif-registry, psa-registry |
| warning | registry | `pds:Document/pds:author_list` | text | naif-registry |
| warning | registry | `pds:Document_File/pds:creation_date_time` | date | temp-atm-registry |
| warning | registry | `pds:Document_File/pds:md5_checksum` | keyword | temp-atm-registry |
| warning | registry | `pds:Element_Array/pds:data_type` | keyword | naif-registry |
| warning | registry | `pds:Element_Array/pds:scaling_factor` | double | naif-registry |
| warning | registry | `pds:Element_Array/pds:unit` | keyword | naif-registry |
| warning | registry | `pds:Element_Array/pds:value_offset` | double | naif-registry, ppi-registry |
| warning | registry | `pds:Encoded_Image/pds:description` | text | naif-registry |
| warning | registry | `pds:Encoded_Image/pds:encoding_standard_id` | keyword | naif-registry |
| warning | registry | `pds:Encoded_Image/pds:offset` | long | naif-registry |
| warning | registry | `pds:External_Reference/pds:description` | text | naif-registry |
| warning | registry | `pds:External_Reference/pds:doi` | keyword | naif-registry |
| warning | registry | `pds:External_Reference/pds:reference_text` | text | naif-registry |
| warning | registry | `pds:Field_Binary/pds:data_type` | keyword | img-registry, naif-registry |
| warning | registry | `pds:Field_Binary/pds:description` | text | img-registry, naif-registry |
| warning | registry | `pds:Field_Binary/pds:field_length` | long | img-registry, naif-registry |
| warning | registry | `pds:Field_Binary/pds:field_location` | long | img-registry, naif-registry |
| warning | registry | `pds:Field_Binary/pds:field_number` | long | img-registry, naif-registry |
| warning | registry | `pds:Field_Binary/pds:name` | keyword | img-registry, naif-registry |
| warning | registry | `pds:Field_Binary/pds:unit` | keyword | img-registry, naif-registry |
| warning | registry | `pds:Field_Character/pds:field_format` | keyword | img-registry |
| warning | registry | `pds:Field_Character/pds:unit` | keyword | img-registry |
| warning | registry | `pds:Field_Delimited/pds:description` | text | naif-registry |
| warning | registry | `pds:Field_Delimited/pds:field_format` | keyword | naif-registry, rms-registry |
| warning | registry | `pds:Field_Delimited/pds:unit` | keyword | naif-registry |
| warning | registry | `pds:File/pds:comment` | text | naif-registry |
| warning | registry | `pds:File/pds:local_identifier` | keyword | naif-registry |
| warning | registry | `pds:File/pds:records` | long | naif-registry |
| warning | registry | `pds:Header/pds:description` | text | naif-registry |
| warning | registry | `pds:Header/pds:local_identifier` | keyword | naif-registry |
| warning | registry | `pds:Internal_Reference/pds:comment` | text | naif-registry |
| warning | registry | `pds:Internal_Reference/pds:lidvid_reference` | keyword | naif-registry |
| warning | registry | `pds:Local_Internal_Reference/pds:local_identifier_reference` | keyword | naif-registry |
| warning | registry | `pds:Local_Internal_Reference/pds:local_reference_type` | keyword | naif-registry |
| warning | registry | `pds:Modification_Detail/pds:description` | text | naif-registry |
| warning | registry | `pds:Modification_Detail/pds:modification_date` | date | naif-registry |
| warning | registry | `pds:Modification_Detail/pds:version_id` | keyword | naif-registry |
| warning | registry | `pds:Observation_Area/pds:comment` | text | en-registry, naif-registry |
| warning | registry | `pds:Observing_System/pds:name` | keyword | naif-registry |
| warning | registry | `pds:Observing_System_Component/pds:description` | text | naif-registry |
| warning | registry | `pds:Person/pds:family_name` | keyword | naif-registry, psa-registry |
| warning | registry | `pds:Person/pds:given_name` | keyword | naif-registry, psa-registry |
| warning | registry | `pds:Person/pds:person_orcid` | keyword | naif-registry, psa-registry |
| warning | registry | `pds:Primary_Result_Summary/pds:description` | text | naif-registry |
| warning | registry | `pds:Record_Binary/pds:fields` | long | img-registry, naif-registry |
| warning | registry | `pds:Record_Binary/pds:groups` | long | img-registry, naif-registry |
| warning | registry | `pds:Record_Binary/pds:record_length` | long | img-registry, naif-registry |
| warning | registry | `pds:Record_Delimited/pds:maximum_record_length` | long | naif-registry |
| warning | registry | `pds:SPICE_Kernel/pds:description` | text | en-registry, sbnumd-registry |
| warning | registry | `pds:SPICE_Kernel/pds:encoding_type` | keyword | en-registry |
| warning | registry | `pds:SPICE_Kernel/pds:kernel_type` | keyword | en-registry |
| warning | registry | `pds:SPICE_Kernel/pds:object_length` | long | en-registry, sbnumd-registry |
| warning | registry | `pds:SPICE_Kernel/pds:offset` | long | en-registry |
| warning | registry | `pds:SPICE_Kernel/pds:parsing_standard_id` | keyword | en-registry |
| warning | registry | `pds:Science_Facets/pds:discipline_name` | keyword | naif-registry |
| warning | registry | `pds:Science_Facets/pds:domain` | keyword | naif-registry, rms-registry |
| warning | registry | `pds:Science_Facets/pds:facet1` | keyword | img-registry, naif-registry |
| warning | registry | `pds:Science_Facets/pds:wavelength_range` | keyword | naif-registry |
| warning | registry | `pds:Source_Product_External/pds:curating_facility` | keyword | naif-registry |
| warning | registry | `pds:Source_Product_External/pds:external_source_product_identifier` | keyword | naif-registry |
| warning | registry | `pds:Source_Product_External/pds:reference_type` | keyword | naif-registry |
| warning | registry | `pds:Source_Product_Internal/pds:lidvid_reference` | keyword | naif-registry, rms-registry |
| warning | registry | `pds:Source_Product_Internal/pds:reference_type` | keyword | naif-registry, rms-registry |
| warning | registry | `pds:Special_Constants/pds:invalid_constant` | keyword | naif-registry, psa-registry |
| warning | registry | `pds:Special_Constants/pds:missing_constant` | keyword | naif-registry |
| warning | registry | `pds:Special_Constants/pds:not_applicable_constant` | keyword | en-registry, naif-registry |
| warning | registry | `pds:Stream_Text/pds:description` | text | naif-registry |
| warning | registry | `pds:Table_Binary/pds:description` | text | img-registry, naif-registry |
| warning | registry | `pds:Table_Binary/pds:name` | keyword | img-registry, naif-registry |
| warning | registry | `pds:Table_Binary/pds:offset` | long | img-registry, naif-registry |
| warning | registry | `pds:Table_Binary/pds:records` | long | img-registry, naif-registry |
| warning | registry | `pds:Table_Character/pds:description` | text | img-registry, naif-registry |
| warning | registry | `pds:Table_Character/pds:name` | keyword | img-registry |
| | | ... and 14 more fields (see mapping_discrepancies.csv) | | |

## Fields mapped with different types

25 fields are mapped with more than one type. Each row lists every type and the nodes that use it; when a field exists on only two indices, neither type is more correct.

| Group | Field | Type: nodes |
|---|---|---|
| registry | `description` | text: en, geo, img, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |
| registry | `ebt:Airmass/ebt:airmass` | double: sbnpsi; keyword: sbnumd |
| registry | `ebt:Airmass/ebt:airmass_time` | date: sbnpsi; keyword: sbnumd |
| registry | `img:Exposure/img:exposure_duration_count` | double: geo, sbnpsi; long: img, temp-atm |
| registry | `insight:Observation_Information/insight:release_number` | integer: en, ppi, temp-atm; keyword: geo |
| registry | `insight:Observation_Information/insight:spacecraft_clock_count_partition` | integer: en, ppi; keyword: geo |
| registry | `nh:Mission_Elapsed_Time/nh:clock_partition` | keyword: sbnumd; long: en |
| registry | `ops:Provenance/ops:registry_sweepers_provenance_version` | integer: en, geo, img, naif, ppi, psa, sbnpsi, sbnumd, temp-atm; keyword: rms |
| registry | `pds:Bundle/pds:description` | text: en, geo, img, ppi, psa, rms, sbnpsi, temp-atm; keyword: naif |
| registry | `pds:Citation_Information/pds:author_list` | text: en, geo, img, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |
| registry | `pds:Citation_Information/pds:description` | text: en, geo, img, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |
| registry | `pds:Collection/pds:description` | text: geo, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |
| registry | `pds:Document/pds:description` | text: en, geo, img, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |
| registry | `pds:Document/pds:document_name` | text: en, geo, img, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |
| registry | `pds:Field_Character/pds:description` | text: en, geo, img, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |
| registry | `pds:SPICE_Kernel/pds:description` | text: geo, img, ppi, psa, rms, sbnpsi, temp-atm; keyword: naif |
| registry | `sb:Exposure/sb:exposure_description` | keyword: sbnumd; text: en |
| registry | `sb:Exposure/sb:exposure_duration` | double: en; keyword: sbnumd |
| registry | `sb:Filter/sb:long_wavelength_limit` | double: en; keyword: sbnumd |
| registry | `sb:Filter/sb:short_wavelength_limit` | double: en; keyword: sbnumd |
| registry | `sb:Instrument_Position_Angles/sb:y_axis_position_angle` | double: en; keyword: sbnumd |
| registry | `sb:Instrument_Position_Angles/sb:z_axis_position_angle` | double: en; keyword: sbnumd |
| registry | `sb:Timing/sb:midobservation_time_UTC_JD` | double: en; keyword: sbnumd |
| registry | `sb:Timing/sb:midobservation_time_UTC_YMD` | date: en; keyword: sbnumd |
| registry | `title` | text: en, geo, img, ppi, psa, rms, sbnpsi, sbnumd, temp-atm; keyword: naif |

