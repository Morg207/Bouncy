#version 330 core

in vec2 fragTexCoord;
out vec4 color;
uniform sampler2D texture1;
uniform vec2 lightPos;
uniform float lightRadius;
uniform vec3 lightColor;
uniform float ambient;
uniform float time;
uniform int isDead;

void main() {
     vec4 texColor = texture(texture1, fragTexCoord);
     float dist = distance(fragTexCoord, lightPos);
     float flicker = 0.9 + 0.2 * sin(time * 12) * sin(time * 18);
     float torchIntensity = flicker * max(0.0,1.0-ambient) * 1.2;
     float intensity = torchIntensity * (1.0 - smoothstep(0.0, lightRadius, dist));
     if(isDead == 1){
        intensity = 0.0;
     }
     vec3 litColor = mix(vec3(0.0),texColor.rgb*lightColor,intensity);
     float shadowFade = (1.0 - smoothstep(0.2, 0.92, intensity));
     litColor.b += (1.0-ambient) * shadowFade * 0.06;
     vec3 amb = texColor.rgb * ambient;
     vec3 finalColor = litColor + amb;
     color = vec4(finalColor, texColor.a);
  }