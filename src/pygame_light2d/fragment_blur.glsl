#version 330 core

in vec2 fragmentTexCoord;
uniform sampler2D imageTexture;

uniform float blurRadius;

out vec4 color;

const float epsilon=.001;

void main()
{
    int kernelSize=int(blurRadius)*2+1;
    vec2 texelSize=1./textureSize(imageTexture,0);
    
    // Gaussian kernel weights
    float weights[64];
    float sum=0.;
    for(int i=0;i<kernelSize;++i){
        float x=float(i)-blurRadius;
        weights[i]=exp(-.5*(x*x)/(blurRadius*blurRadius));
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
            vec2 sampleTexCoord=fragmentTexCoord+offset;
            sampleTexCoord=clamp(sampleTexCoord,vec2(epsilon),vec2(1-epsilon));
            float w=weights[x+int(blurRadius)]*weights[y+int(blurRadius)];
            blurredColor+=texture(imageTexture,sampleTexCoord)*w;
        }
    }
    
    color=blurredColor;
}
