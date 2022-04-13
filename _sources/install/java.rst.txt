=================
Java Installation
=================


Overview
********

Java is required to run many Registry components and tools such as Harvest, Registry Manager, 
and API Server. 

Only **Java 11** is supported. 
Some applications, like Harvest or Registry Manager will not run with **Java 1.8**.


Test if Java is already installed
*********************************

To test if Java is already installed on your system, run the following command in a terminal::

   java -version


If Java is already installed, you will see a message similar to this::

   openjdk version "11.0.5" 2019-10-15
   OpenJDK Runtime Environment 18.9 (build 11.0.5+10)
   OpenJDK 64-Bit Server VM 18.9 (build 11.0.5+10, mixed mode)

.. note::
   Your system might have multiple versions of Java installed, for example, JDK 1.8 and JDK 11.
   If JDK 11 is not the default, then set **JAVA_HOME** environment variable to point to JDK 11 before running 
   Harvest or Registry Manager.


Installation
************

There are several distributions of Java:

* **Open JDK** (Free) can be downloaded from different sites, for example, 
  `adoptopenjdk.net <https://adoptopenjdk.net/>`_ or 
  `azul.com <https://www.azul.com/downloads/zulu-community>`_.
  Most Linux distributions have Open JDK in their standard repositories.

* **Oracle JDK** (Commercial) can be downloaded from 
  `www.oracle.com <https://www.oracle.com/java/technologies/javase-jdk11-downloads.html>`_.
  You must register and accept a license to download.


We recommend installing **OpenJDK**. Sites listed above have detailed installation instructions. 

