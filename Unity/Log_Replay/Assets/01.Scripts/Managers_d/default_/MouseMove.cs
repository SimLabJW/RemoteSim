using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MouseMove : MonoBehaviour
{
    public float sensitivity = 500f;
    //���콺 �ΰ���
    public float rotationX;
    public float rotationY;

    void Start()
    {

    }

    void Update()
    {
        float MouseMoveX = Input.GetAxis("Mouse X");
        //���콺 x�� �����Ӱ� �޾Ƽ� ����
        float MouseMoveY = Input.GetAxis("Mouse Y");
        //���콺 y�� �����Ӱ� �޾Ƽ� ����

        rotationY += MouseMoveX * sensitivity * Time.deltaTime;
        rotationX += MouseMoveY * sensitivity * Time.deltaTime;

        if (rotationX > 35f)
        //�� �ʹ� �ȿö󰡰�
        {
            rotationX = 35f;
        }

        if (rotationX < -30f)
        //�� �ʹ� �ȼ�������
        {
            rotationX = -30f;
        }

        transform.eulerAngles = new Vector3(-rotationX, rotationY, 0);
    }

}
