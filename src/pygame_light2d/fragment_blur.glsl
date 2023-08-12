#version 330 core

in vec2 fragmentTexCoord;// holds the Vertex position <-1,+1> !!!
uniform sampler2D imageTexture;// used texture unit

// uniform width;
// uniform height;

// uniform vec2 lightPos;

out vec4 color;

const float blurRadius=6.;
const int kernelSize=int(blurRadius)*2+1;

const float blurAttenuation=6.;// Increase this number to make it SHARPER

void main()
{
    vec2 texelSize=1./textureSize(imageTexture,0);
    
    // Blur strength
    // vec2 diff=lightPos-fragmentTexCoord;
    // float blurStrength=1.+1./(blurAttenuation*dot(diff,diff)+.1);
    float blurStrength=1.+1./(blurAttenuation+.1);
    
    // Gaussian kernel weights
    float weights[kernelSize];
    float sum=0.;
    for(int i=0;i<kernelSize;++i){
        float x=float(i)-blurRadius;
        weights[i]=exp(-.5*(x*x)*blurStrength/(blurRadius*blurRadius));
        sum+=weights[i];
    }
    
    // Normalize the weights
    for(int i=0;i<kernelSize;++i){
        weights[i]/=sum;
    }
    
    vec4 blurredColor=vec4(0.);
    for(int x=-int(blurRadius);x<=int(blurRadius);++x){
        for(int y=-int(blurRadius);y<=int(blurRadius);++y){
            vec2 offset=vec2(float(x),float(y))*texelSize;
            float w=weights[x+int(blurRadius)]*weights[y+int(blurRadius)];
            blurredColor+=texture(imageTexture,fragmentTexCoord+offset)*w;
        }
    }
    
    color=blurredColor;
}
