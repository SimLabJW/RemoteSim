using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class PrefabTest : MonoBehaviour
{
    //1�� ��� 
    //public GameObject prefab;

    //2�� ���
    GameObject prefab;
    //2,3�� ����
    GameObject tank;

    // Start is called before the first frame update
    void Start()
    {
        ////2������
        //prefab = Resources.Load<GameObject>("01.Prefab/Tank");

        ////1,2�� ����
        //tank = Instantiate(prefab);

        //3�� : resource Manager�� ���� ����
        //tank = Managers.Resource.Instantiate("Tank");

        //Destroy(tank,3.0f);
        
    }

}
