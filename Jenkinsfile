node {
    stage('checkout'){
        checkout scm
    }
    stage('docker build'){
        def customImage = docker.build('peeps:latest','--network=host -f deployment/nginx/Dockerfile .')
    }
    stage('docker update'){
        sh '''#!/bin/bash
            docker rm -f peeps
            docker run -d --name peeps -p 0.0.0.0:8080:8080 -t peeps:latest
        '''
    }

}