// include file for adapting rt/shader created .fx files

#include "stdinclude.fxh"

BW_SPECULAR_LIGHTING

float2x3 LightArray(		
		uniform int nDirectionals,
		float4 surfPos,
		float3 surfNorm,
		float4 eyePos,
		float specPow)
{
	float2x3 illum = float2x3(0, 0, 0, 0, 0, 0);	
	float3 eyeVec = normalize(eyePos.xyz-surfPos);
	for (int i = 0;i<nDirectionals; i = (i+1))
	{
		float3 lightVect = specularDirectionalLights[i].direction;
		float3 halfVec = normalize(lightVect+eyeVec);
		float NdotL = dot(lightVect, surfNorm);
		float NdotH = dot(surfNorm, halfVec);
		float4 l = lit(NdotL, NdotH, specPow);
		illum[0] = (illum[0]+(l.y*specularDirectionalLights[i].colour.xyz));
		illum[1] = (illum[1]+(l.z*specularDirectionalLights[i].colour.xyz));
	};
	return illum;
}