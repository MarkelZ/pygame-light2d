#version 330 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// used texture unit

uniform int native_width;
uniform int native_height;

uniform vec2 lightPos;

uniform hullVSSBO{
    float hullV[2048];
};

uniform hullIndSSBO{
    int hullInd[256];
};
uniform int numHulls;

uniform vec4 lightCol;
uniform float lightPower;
uniform float radius;
uniform bool castShadows;

out vec4 color;

vec2 uv_to_world(vec2 v){
    return vec2(native_width*v.x,native_height*v.y);
}

bool isOcluded(vec2 p,vec2 q){
    vec2 v1=q-p;
    vec2 v2=lightPos-fragmentTexCoord;
    float crossProduct=v1.x*v2.y-v1.y*v2.x;
    float dotProduct=v1.x*v2.x+v1.y*v2.y;
    float lengthV1=length(v1);
    float lengthV2=length(v2);
    float t=(v2.x*(p.y-fragmentTexCoord.y)+v2.y*(fragmentTexCoord.x-p.x))/crossProduct;
    vec2 intersection=p+t*v1;
    if(crossProduct==0.){
        return false;
    }
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
    
    // Skip if fragment is too far away from light source
    vec2 diff=uv_to_world(lightPos-fragmentTexCoord);
    float dist=sqrt(diff.x*diff.x+diff.y*diff.y);
    if(dist>=radius){
        return;
    }
    
    // Check if ocluded by a hull
    bool ocluded=false;
    if(castShadows){
        int prev=0;
        for(int i=0;i<numHulls;i++){
            int j0=prev;
            int jn=hullInd[i];
            int n=jn-j0;
            for(int j=j0;j<jn;j++){
                int ind1=j*2;
                int ind2=(((j+1-j0)%n)+j0)*2;
                vec2 p=vec2(hullV[ind1],hullV[ind1+1]);
                vec2 q=vec2(hullV[ind2],hullV[ind2+1]);
                if(isOcluded(p,q)){
                    ocluded=true;
                    break;
                }
            }
            prev=hullInd[i];
        }
    }
    
    // Brighten up if not ocluded
    if(!ocluded){
        // Cubic spline for light intensity
        float a=2/(radius*radius*radius);
        float b=-3/(radius*radius);
        float intensity=a*dist*dist*dist+b*dist*dist+1;
        // intensity=sqrt(intensity);
        
        // Blend light color
        vec4 lightVal=lightCol*intensity*lightPower;
        float alpha=lightVal[3];
        color+=vec4(lightVal.xyz*alpha,alpha);
    }
    
}
