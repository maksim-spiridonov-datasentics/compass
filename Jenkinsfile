library identifier: 'dbx-jenkins-shared-lib@v1.0.0', retriever: modernSCM(
  [
    $class: 'GitSCMSource',
    remote: 'ssh://git@stash.s-mxs.net:7999/cs-dbx/dbx-jenkins-shared-lib.git',
    credentialsId: 'CHOPSUEY_JENKINS_SSH'
  ]
) _

pipeline {
    agent { label 'dbx-python311' }

    stages {
      stage("Build"){
        steps {
          echo "Building the project...TODO"
          // checkPoetryLock()
          // checkRequirements()
          // buildVirtualEnvironment()
          // sh "cp requirements.txt usecases/bia-usecase/requirements.txt"
        }
      }
      stage("Validate TEST") {
        when {
          branch 'develop'
        }
        environment {
          DATABRICKS_CLIENT_ID = credentials('DATABRICKS_CLIENT_ID_GNAI_FAT')
          DATABRICKS_CLIENT_SECRET = credentials('DATABRICKS_CLIENT_SECRET_GNAI_FAT')
        }
        steps {
          sh "databricks bundle validate --target test_gnai"
        }
      }
      stage("Deploy TEST") {
        when {
          branch 'develop'
        }
        environment {
          DATABRICKS_CLIENT_ID = credentials('DATABRICKS_CLIENT_ID_GNAI_FAT')
          DATABRICKS_CLIENT_SECRET = credentials('DATABRICKS_CLIENT_SECRET_GNAI_FAT')
        }
        steps {
          sh "databricks bundle deploy --target test_gnai"
          sh "databricks bundle run deploy_agent --target test_gnai"
        }
      }
      stage("Validate FAT") {
        when {
            branch 'release-v*'
        }
        environment {
          DATABRICKS_CLIENT_ID = credentials('DATABRICKS_CLIENT_ID_GNAI_FAT')
          DATABRICKS_CLIENT_SECRET = credentials('DATABRICKS_CLIENT_SECRET_GNAI_FAT')
        }
        steps {
          sh "databricks bundle validate --target lab_gnai"
        }
      }
      stage("Deploy LAB") {
        when {
            branch 'release-v*'
        }
        environment {
          DATABRICKS_CLIENT_ID = credentials('DATABRICKS_CLIENT_ID_GNAI_FAT')
          DATABRICKS_CLIENT_SECRET = credentials('DATABRICKS_CLIENT_SECRET_GNAI_FAT')
        }
        steps {
          sh "databricks bundle deploy --target lab_gnai"
          sh "databricks bundle run deploy_agent --target lab_gnai"
        }
      }
      //stage("Validate PROD") {
      //  when {
      //    branch 'main'
      //  }
      //  environment {
      //    DATABRICKS_CLIENT_ID = credentials('DATABRICKS_CLIENT_ID_AIF_PROD')
      //    DATABRICKS_CLIENT_SECRET = credentials('DATABRICKS_CLIENT_SECRET_AIF_PROD')
      //  }
      //  steps {
      //    sh "databricks bundle validate --target prod_aif"
      //  }
      // }
      //stage("Deploy PROD") {
      //  when {
      //    branch 'main'
      //  }
      //  environment {
      //    DATABRICKS_CLIENT_ID = credentials('DATABRICKS_CLIENT_ID_AIF_PROD')
      //    DATABRICKS_CLIENT_SECRET = credentials('DATABRICKS_CLIENT_SECRET_AIF_PROD')
      //  }
      //  steps {
      //    sh "databricks bundle deploy --target prod_aif"
      //  }
      // }
    }
  }