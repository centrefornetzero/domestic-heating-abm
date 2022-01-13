{
  apiVersion: 'batch/v1',
  kind: 'Job',
  metadata: {
    name: std.extVar('JOB_NAME')
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
          },
        ],
        restartPolicy: 'Never',
        nodeSelector: {
          'cloud.google.com/gke-spot': 'true',
        },
      },
    },
  },
}
