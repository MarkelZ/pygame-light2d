#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;

uniform sampler2D lightmap;

uniform vec4 ambient;

uniform float maxLuminosity=2.5f;

out vec4 color;

void main()
{
    vec4 texcolor=texture(imageTexture,fragmentTexCoord);
    vec4 lightVal=texture(lightmap,fragmentTexCoord);
    
    lightVal=clamp(lightVal,0,maxLuminosity);
    
    color=texcolor*(ambient+lightVal);
}