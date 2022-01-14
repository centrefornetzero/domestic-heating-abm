{
  apiVersion: 'batch/v1',
  kind: 'Job',
  metadata: {
    name: std.extVar('JOB_NAME'),
    namespace: 'domestic-heating-abm'
  },
  spec: {
    template: {
      spec: {
        containers: [
          {
            name: 'domestic-heating-abm',
            image: std.extVar('IMAGE_URI'),
            command: ['python', '-m', 'simulation'],
            args: ['-h'],
            env: {
              PROJECT_ID: std.extVar('PROJECT_ID'),
            },
          },
        ],
        restartPolicy: 'Never',
        nodeSelector: {
          'cloud.google.com/gke-spot': 'true',
        },
        serviceAccountName: 'runner'
      },
    },
  },
}
