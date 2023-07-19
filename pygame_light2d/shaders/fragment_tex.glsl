#version 450 core

in vec2 fragmentTexCoord;// top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture;// used texture unit

out vec4 color;

void main()
{
    vec4 color=texture(imageTexture,fragmentTexCoord);
}
