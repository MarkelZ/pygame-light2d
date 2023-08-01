#version 450 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// used texture unit

// uniform width;
// uniform height;

uniform sampler2D lightmap;

// const vec4 ambient=vec4(.2);
// const vec4 ambient=vec4(0.,0.,0.,.2);

uniform vec4 ambient;

out vec4 color;

void main()
{
    vec4 texcolor=texture(imageTexture,fragmentTexCoord);
    vec4 lightVal=texture(lightmap,fragmentTexCoord);
    color=texcolor*(ambient[3]+lightVal[3])+ambient+lightVal;
    color=texcolor*(ambient+lightVal);
}
