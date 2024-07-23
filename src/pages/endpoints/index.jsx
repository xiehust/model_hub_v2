// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React, { useEffect, useRef, useState } from 'react';
import intersection from 'lodash/intersection';
import Pagination from '@cloudscape-design/components/pagination';
import Table from '@cloudscape-design/components/table';
import TextFilter from '@cloudscape-design/components/text-filter';
import { COLUMN_DEFINITIONS, DEFAULT_PREFERENCES, Preferences } from './table-config';
import { Breadcrumbs, endpointsBreadcrumbs } from '../commons/breadcrumbs'
import { CustomAppLayout, Navigation, Notifications, TableNoMatchState } from '../commons/common-components';
import { FullPageHeader } from './full-page-header';
import { useLocalStorage } from '../commons/use-local-storage';
import {
  getHeaderCounterServerSideText,
  distributionTableAriaLabels,
  getTextFilterCounterServerSideText,
  renderAriaLive,
} from '../../i18n-strings';
import { useColumnWidths } from '../commons/use-column-widths';
import { useDistributions } from './hooks';
import { TopNav } from '../commons/top-nav';
import { remotePost } from '../../common/api-gateway';
import {DeleteModelModal} from '../endpoints/delete-ed';
import '../../styles/base.scss';

function ServerSideTable({
  columnDefinitions,
  saveWidths,
  loadHelpPanelContent,
  setDisplayNotify,
  setNotificationData
}) {
  const [preferences, setPreferences] = useLocalStorage('ModelHub-endpoint-table-Preferences', DEFAULT_PREFERENCES);
  const [descendingSorting, setDescendingSorting] = useState(false);
  const [currentPageIndex, setCurrentPageIndex] = useState(1);
  const [filteringText, setFilteringText] = useState('');
  const [delayedFilteringText, setDelayedFilteringText] = useState('');
  const [sortingColumn, setSortingColumn] = useState(columnDefinitions[0]);
  const [refresh,setRefresh] = useState(false);
  const [visible, setVisible] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);
  const [data,setData] = useState();
  const { pageSize } = preferences;
  const params = {
    pagination: {
      currentPageIndex,
      pageSize,
    },
    sorting: {
      sortingColumn,
      sortingDescending: descendingSorting,
    },
    filtering: {
      filteringText: delayedFilteringText,
    },
    refresh:refresh
  };
  const { items, loading, totalCount, pagesCount, currentPageIndex: serverPageIndex } = useDistributions(params);

  useEffect(() => {
    setSelectedItems(oldSelected => intersection(items, oldSelected));
  }, [items]);

  const onSortingChange = event => {
    setDescendingSorting(event.detail.isDescending);
    setSortingColumn(event.detail.sortingColumn);
  };

  const onClearFilter = () => {
    setFilteringText('');
    setDelayedFilteringText('');
  };

  const onDelete =()=>{
    setVisible(true);
  }

  const onRefresh = () => {
    setRefresh((prev)=>!prev);
  };


  return (
    <div>
    {visible&&<DeleteModelModal setDisplayNotify={setDisplayNotify} setNotificationData={setNotificationData}
    selectedItems={selectedItems} setVisible={setVisible} visible={visible}/>}

    <Table
      enableKeyboardNavigation={true}
      loading={loading}
      selectedItems={selectedItems}
      items={items}
      onSortingChange={onSortingChange}
      onSelectionChange={event => setSelectedItems(event.detail.selectedItems)}
      sortingColumn={sortingColumn}
      sortingDescending={descendingSorting}
      columnDefinitions={columnDefinitions}
      columnDisplay={preferences.contentDisplay}
      ariaLabels={distributionTableAriaLabels}
      renderAriaLive={renderAriaLive}
      selectionType="single"
      variant="full-page"
      stickyHeader={true}
      resizableColumns={true}
      onColumnWidthsChange={saveWidths}
      wrapLines={preferences.wrapLines}
      stripedRows={preferences.stripedRows}
      contentDensity={preferences.contentDensity}
      stickyColumns={preferences.stickyColumns}
      header={
        <FullPageHeader
          selectedItemsCount={selectedItems.length}
          selectedItems={selectedItems}
          onDelete = {onDelete}
          setNotificationData = {setNotificationData}
          setDisplayNotify = {setDisplayNotify}
          counter={!loading && getHeaderCounterServerSideText(totalCount, selectedItems.length)}
          onInfoLinkClick={loadHelpPanelContent}
          onRefresh={onRefresh}
        />
      }
      loadingText="Loading"
      empty={<TableNoMatchState onClearFilter={onClearFilter} />}
      filter={
        <TextFilter
          filteringText={filteringText}
          onChange={({ detail }) => setFilteringText(detail.filteringText)}
          onDelayedChange={() => setDelayedFilteringText(filteringText)}
          filteringAriaLabel="Filter"
          filteringPlaceholder="Find"
          filteringClearAriaLabel="Clear"
          countText={getTextFilterCounterServerSideText(items, pagesCount, pageSize)}
        />
      }
      pagination={
        <Pagination
          pagesCount={pagesCount}
          currentPageIndex={serverPageIndex}
          disabled={loading}
          onChange={event => setCurrentPageIndex(event.detail.currentPageIndex)}
        />
      }
      preferences={<Preferences preferences={preferences} setPreferences={setPreferences} />}
    />
  </div>
  );
}

function EndpointsTable() {
  const [columnDefinitions, saveWidths] = useColumnWidths('React-Endpointtable-Widths', COLUMN_DEFINITIONS);
  const [toolsOpen, setToolsOpen] = useState(false);
  const [notificationData, setNotificationData] = useState({});
  const [displayNotify, setDisplayNotify] = useState(false);


  const appLayout = useRef();
  return (
    <div>
      <TopNav />
      <CustomAppLayout
        ref={appLayout}
        navigation={<Navigation activeHref="/endpoints" />}
        notifications={<Notifications successNotification={displayNotify} data={notificationData} />}
        breadcrumbs={<Breadcrumbs items={endpointsBreadcrumbs} />}
        content={
          <div>
          <ServerSideTable
            setNotificationData={setNotificationData}
            setDisplayNotify={setDisplayNotify}
            columnDefinitions={columnDefinitions}
            saveWidths={saveWidths}
            loadHelpPanelContent={() => {
              setToolsOpen(true);
              appLayout.current?.focusToolsClose();
            }}
          />
          </div>
        }
        contentType="table"
        toolsOpen={toolsOpen}
        onToolsChange={({ detail }) => setToolsOpen(detail.open)}
      />
     
    </div>
  );
}


export default EndpointsTable;

