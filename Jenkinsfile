/*
 * Copyright © 2022, California Institute of Technology ("Caltech").
 * U.S. Government sponsorship acknowledged.
 * 
 * All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 
 * • Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 * • Redistributions must reproduce the above copyright notice, this list of
 * conditions and the following disclaimer in the documentation and/or other
 * materials provided with the distribution.
 * • Neither the name of Caltech nor its operating division, the Jet Propulsion
 * Laboratory, nor the names of its contributors may be used to endorse or
 * promote products derived from this software without specific prior written
 * permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

// Declarative pipeline for continuous deployment of the Registry
pipeline {

    // We want this to run completely on pds-expo.jpl.nasa.gov
    agent { node('pds-expo') }

    // Environment variables
    environment {
        // Pipeline-Specific Environtment
        // ------------------------------
        //
        // How long to wait (in seconds) before killing containers:
        shutdown_timeout = "30"
        // Simplified `docker-compose` command:
        compose = "docker-compose --profile int-registry-service-loader --project-name registry --file ${env.WORKSPACE}/docker/docker-compose.yml"

        // Registry-Specific Environment
        // -----------------------------
        //
        // Registry API properties; we generate this file in the build step
        REG_API_APP_PROPERTIES_FILE = "${env.WORKSPACE}/app.props"

        // Where to harvest the data from
        HARVEST_DATA_DIR = "${env.WORKSPACE}/test-data/registry-harvest-data"
    }

    options {
        disableConcurrentBuilds()
        skipStagesAfterUnstable()
    }

    stages {
        stage('🧱 Build') {
            // It's already built pe se, but we want a clean environment each time we deploy and with the
            // precisely same test data as in the source repository, so the "build" step here is more like
            // a "clean" step.
            steps {
                sh "install --directory ${env.HARVEST_DATA_DIR}"
                dir(${env.HARVEST_DATA_DIR}) {
                    sh "find . -delete"
                }
                sh "sed -e s/8080/19999/ < ${env.WORKSPACE}/docker/application.properties > ${env.WORKSPACE}/app.props"
                sh "printenv"
                sh "pwd"
                echo "That's all folks 🎬"
            }
        }
        stage('🩺 Test') {
            // The repository is already tested so there's nothing that needs to be done; However,
            // we include the stage for reporting purposes (all pipelines should have a test
            // stage).
            steps {
                echo 'No-op test step: ✓'
            }
        }
        stage('🚀 Deploy') {
            steps {
                sh "$compose down --remove-orphans --timeout ${shutdown_timeout} ||:"
                // 🔮 TODO: Include --no-color? 
                // sh "$compose up --detach --quiet-pull --timeout ${shutdown_timeout}"
            }

            // 🔮 TODO: Include a `post {…}` block to do post-deployment test queries?
        }
    }
}
