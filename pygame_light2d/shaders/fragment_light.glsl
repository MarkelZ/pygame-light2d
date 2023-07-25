#version 450 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// used texture unit

// uniform width;
// uniform height;

uniform vec2 lightPos;

uniform vec2 p1;
uniform vec2 p2;
uniform vec2 p3;
uniform vec2 p4;

uniform vec4 lightCol;
uniform float lightPower;
uniform float decay;

out vec4 color;

bool isOcluded(vec2 p,vec2 q){
    vec2 v1=q-p;
    vec2 v2=lightPos-fragmentTexCoord;
    float crossProduct=v1.x*v2.y-v1.y*v2.x;
    float dotProduct=v1.x*v2.x+v1.y*v2.y;
    float lengthV1=length(v1);
    float lengthV2=length(v2);
    float t=(v2.x*(p.y-fragmentTexCoord.y)+v2.y*(fragmentTexCoord.x-p.x))/crossProduct;
    vec2 intersection=p+t*v1;
    if(distance(p,intersection)>lengthV1||distance(q,intersection)>lengthV1){
        return false;// The intersection point is not between p and q
    }
    if(distance(fragmentTexCoord,intersection)>lengthV2||distance(lightPos,intersection)>lengthV2){
        return false;// The intersection point is not between fragmentTexCoord and lightPos
    }
    return true;
}

void main()
{
    color=texture(imageTexture,fragmentTexCoord);
    
    vec2[]points=vec2[](p1,p2,p3,p4);
    int n=4;
    bool ocluded=false;
    for(int i=0;i<n;i++){
        vec2 p=points[i];
        vec2 q=points[(i+1)%n];
        if(isOcluded(p,q)){
            ocluded=true;
            break;
        }
    }
    
    if(!ocluded){
        vec2 diff=lightPos-fragmentTexCoord;
        float dist=diff.x*diff.x+diff.y*diff.y;
        float intensity=1./(decay*dist+1.);
        // TO REMOVE THE WEIRD CIRCLE AROUND LIGHT,
        // MAYBE SUBTRACT ISTEAD OF ADD
        color+=lightCol*intensity*lightPower;
    }
}
