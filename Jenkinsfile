node {
    stage('checkout'){
        checkout scm
    }
    stage('docker build'){
        def version = readFile('VERSION')
        def versions = version.split('\\.')
        def major = versions[0]
        def minor = versions[0] + '.' + versions[1]
        def patch = version.trim()
        
        def customImage = docker.build('peeps:'+version,' -f deployment/nginx/Dockerfile .')

    }
    stage('docker update'){
        sh '''#!/bin/bash
            
            docker rm -f peeps
            docker run -d --name peeps -p 0.0.0.0:8080:8080 -t peeps:${version}
        '''
    }

}