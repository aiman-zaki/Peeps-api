node {
    stage('checkout'){
        checkout scm
    }
    stage('docker build'){
        def version = readFile('VERSION')        
        def customImage = docker.build('peeps:'+version,' -f deployment/nginx/Dockerfile .')

    }
    stage('docker update'){
        def version = readFile('VERSION')
        sh """#!/bin/bash
            
            docker rm -f peeps
            docker run -d --name peeps -p 0.0.0.0:8080:8080 -t peeps:${version}
        """
    }

}