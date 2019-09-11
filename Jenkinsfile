pipeline {
    agent any
    stages {
        stage ('Checkout') {
            steps{
                checkout scm
            }
        }
        stage ('docker build') {
            steps {
                script {
                    def customImage = docker.build('peeps:latest','-f deployment/nginx/Dockerfile .')
                }
            }
        }
        
    }
}