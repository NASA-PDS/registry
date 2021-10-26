# PDS Registry Manager Elastic

The [Planetary Data System](https://pds.nasa.gov/) (PDS) Registry Manager Elastic provides functionality for configuring the PDS Registry Elastic. It's a sub-component of the PDS Registry App (https://github.com/NASA-PDS/pds-registry-app).


## Documentation

The documentation for the latest release of the PDS Registry (of which this software is a component)—including release notes, installation, and operation—is online at https://nasa-pds.github.io/pds-registry-app/.


## Build

The software can be compiled and built with the `mvn compile` command but in order to create the JAR file, you must execute the `mvn compile jar:jar` command.

In order to create a complete distribution package, execute the following commands: 
```
% mvn site
% mvn package
```

## Release

Thanks to [GitHub Actions](https://github.com/features/actions) and the [Roundup Action](https://github.com/NASA-PDS/roundup-action), this software is automatically released to the Maven Central Repository.

But if you need to do this manually, the procedure is described below.


### Pre-Requisites

- Make sure you have your GPG Key created and sent to server.
- Make sure you have your `.settings` configured correctly for GPG:
```xml
<profiles>
  <profile>
    <activation>
      <activeByDefault>true</activeByDefault>
    </activation>
    <properties>
      <gpg.executable>gpg</gpg.executable>
      <gpg.keyname>KEY_NAME</gpg.keyname>
      <gpg.passphrase>KEY_PASSPHRASE</gpg.passphrase>
    </properties>
  </profile>
</profiles>
```


### Operational Release

1. Checkout the dev branch.
2. Version the software:
```console
$ mvn versions:set -DnewVersion=1.2.0
```

3. Deploy software to Sonatype Maven repo:
```console
$ # Operational release
$ mvn clean site deploy -P release
```

4. Create pull request from dev → main and merge.
5. Tag release in Github
6. Update version to next snapshot:
```console
$ mvn versions:set -DnewVersion=1.3.0-SNAPSHOT
```

### Snapshot Release

1. Checkout the dev branch.
2. Deploy software to Sonatype Maven repo:
```console
$ # Operational release
$ mvn clean site deploy
```

## Maven JAR Dependency Reference

This setion describes the Java jar dependencies.

### Official Releases

https://search.maven.org/search?q=g:gov.nasa.pds%20AND%20a:registry&core=gav

### Snapshots

https://oss.sonatype.org/content/repositories/snapshots/gov/nasa/pds/registry/

👉 **Note:** the above link may be broken.

If you want to access snapshots, add the following to your `~/.m2/settings.xml`:
```xml
<profiles>
  <profile>
     <id>allow-snapshots</id>
     <activation><activeByDefault>true</activeByDefault></activation>
     <repositories>
       <repository>
         <id>snapshots-repo</id>
         <url>https://oss.sonatype.org/content/repositories/snapshots</url>
         <releases><enabled>false</enabled></releases>
         <snapshots><enabled>true</enabled></snapshots>
       </repository>
     </repositories>
   </profile>
</profiles>
```


## 📃 License

The project is licensed under the [Apache version 2](LICENSE.md) license.
