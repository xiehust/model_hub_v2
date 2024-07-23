// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React ,{useState} from 'react';
import { Button, Modal, Box,  SpaceBetween, } from '@cloudscape-design/components';
import { remotePost } from '../../common/api-gateway';
import { useTranslation } from "react-i18next";

interface PageHeaderProps {
  extraActions?: React.ReactNode;
  selectedItems:ReadonlyArray<any>,
  visible: boolean;
  setVisible: (value: boolean) => void;
  setDisplayNotify: (value: boolean) => void;
  setNotificationData: (value: any) => void;
  onDelete?: () => void;
  onRefresh?: () => void;
}


export const DeleteModelModal = ({
    extraActions = null,
    selectedItems,
    visible,
    setVisible,
    setDisplayNotify,
    setNotificationData,
    ...props
  }: PageHeaderProps) => {
    const { t } = useTranslation();
    const endpoint_name = selectedItems[0].endpoint_name

    const onDeloyConfirm =()=>{
        
        const fromData = {endpoint_name:endpoint_name}
        remotePost(fromData, 'delete_endpoint').
        then(res => {
            if (res.response.result) {
            //   console.log(res.response)
              setVisible(false);
              setDisplayNotify(true);
              setNotificationData({ status: 'success', content: `Delete Endpoint :${endpoint_name} Success` });
            }else{
                setVisible(false);
                setDisplayNotify(true);
                setNotificationData({ status: 'error', content: `Delete Endpoint :${endpoint_name} Failed` });
            }
        
        })
        .catch(err => {
          setDisplayNotify(true);
          setVisible(false);
          setNotificationData({ status: 'error', content: `Delete Endpoint failed` });
        })
    }
    return (
      <Modal
        onDismiss={() => setVisible(false)}
        visible={visible}
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={()=> setVisible(false)}>Cancel</Button>
              <Button variant="primary" onClick={onDeloyConfirm}>Confirm</Button>
            </SpaceBetween>
          </Box>
        }
        header="Delete endpoint"
      >
        {`Confirm to delete endpoint:${endpoint_name}` }
      </Modal>
    );
  }