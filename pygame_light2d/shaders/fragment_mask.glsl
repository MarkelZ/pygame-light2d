#version 450 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// used texture unit

// uniform width;
// uniform height;

uniform sampler2D lightmap;

// const vec4 ambient=vec4(.2);
const vec4 ambient=vec4(0,0,0,.25);

out vec4 color;

void main()
{
    vec4 texcolor=texture(imageTexture,fragmentTexCoord);
    vec4 lightVal=texture(lightmap,fragmentTexCoord);
    // color=texcolor*(lightVal+ambient)+.5*lightVal;
    color=texcolor*ambient[3]+ambient+(texcolor+.5)*lightVal;
    
    // DEBUG
    if(lightVal[3]!=1.){
        color=vec4(1.,0.,1.,1.);
    }
}
