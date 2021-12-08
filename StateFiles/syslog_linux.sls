

# installation des prerequis
verifier packages pre-requis:
  pkg.installed:
    - pkgs:
      - rsyslog


# configuration du syslog
config syslog:
  file.append:
    - name: '/etc/rsyslog.conf'
    - text:
      #- "*.* @@vrli.cpod-vrealize.az-fkd.cloud-garage.net:514"
      - "*.* @@{{pillar['serveur_VRLI']}}:{{pillar['port_VRLI']}}"
    - require:
      - verifier packages pre-requis


# redemarre le service rsyslog si necessaire (si changement de config du fichier):
restart rsyslog service:
  service.running:
    - name: rsyslog
    - watch:
      - file: /etc/rsyslog.conf



