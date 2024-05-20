using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using UnityEngine.Rendering;

public class InverssphereRendering : MonoBehaviour
{

    //[SerializeField]
    //GameObject inversesphere;

    //public Texture2D imageTexture;
    public Renderer cuberenderer;

    private byte[] bytes;

    private byte[] before_;


    // Start is called before the first frame update
    void Start()
    {
        one_time_rendering();

    }

    // �̹��� ������ byte �迭�� �ε��ϴ� �Լ�



    //// Update is called once per frame
    void Update()
    {
        if (before_ != GameManager.Communication.received_message)
        {
            bytes = GameManager.Communication.received_message;
            Texture2D texture = new Texture2D(2, 2);
            texture.LoadImage(bytes);
            
            texture.Apply();
            cuberenderer.material.mainTexture = texture;
            cuberenderer.enabled = true;

            before_ = bytes;
        }

    }

    void one_time_rendering()
    {
        //Debug.Log(GameManager.Communication.received_message);
        if (GameManager.Communication.received_message != null)
        {
            Debug.Log("Received Image Data");
            


            try
            {
                // Base64�� ���ڵ��� ���ڿ��� ����Ʈ�� ��ȯ
                bytes = GameManager.Communication.received_message;
                before_ = bytes;
                Texture2D texture = new Texture2D(2, 2);
                 // �ӽ� ũ��
                //Convert.FromBase64String(System.Text.Encoding.UTF8.GetString(bytes))
                if (texture.LoadImage(bytes))
                {
                    texture.Apply();
                    cuberenderer.material.mainTexture = texture;
                    cuberenderer.enabled = true;
                    //first_time = true;
                }
                else
                {
                    Debug.LogError("Failed to create texture from received bytes");
                }
            }
            catch (FormatException fe)
            {
                Debug.LogError("Received string is not a valid Base64: " + fe.Message);
            }
        }


        //first_time = true;

    }

    void etc_time_rendering()
    {
        Debug.Log("-ing");
    }
}
