import { useMemo, useState } from "react";

import { SingleSelector } from "@/lib/components/ui/SingleSelector/SingleSelector";
import { Tabs } from "@/lib/components/ui/Tabs/Tabs";
import { requiredRolesForUpload } from "@/lib/config/upload";
import { useBrainContext } from "@/lib/context/BrainProvider/hooks/useBrainContext";
import { useKnowledgeToFeedContext } from "@/lib/context/KnowledgeToFeedProvider/hooks/useKnowledgeToFeedContext";
import { Tab } from "@/lib/types/Tab";

import styles from "./KnowledgeToFeed.module.scss";
import { FromDocuments } from "./components/FromDocuments/FromDocuments";
import { FromWebsites } from "./components/FromWebsites/FromWebsites";
import { formatMinimalBrainsToSelectComponentInput } from "./utils/formatMinimalBrainsToSelectComponentInput";

export const KnowledgeToFeed = (): JSX.Element => {
  const { allBrains, setCurrentBrainId, currentBrain } = useBrainContext();
  const [selectedTab, setSelectedTab] = useState("From documents");
  const { knowledgeToFeed } = useKnowledgeToFeedContext();

  const brainsWithUploadRights = formatMinimalBrainsToSelectComponentInput(
    useMemo(
      () =>
        allBrains.filter((brain) =>
          requiredRolesForUpload.includes(brain.role)
        ),
      [allBrains]
    )
  );

  const knowledgesTabs: Tab[] = [
    {
      label: "From documents",
      isSelected: selectedTab === "From documents",
      onClick: () => setSelectedTab("From documents"),
      iconName: "edit",
    },
    {
      label: "From websites",
      isSelected: selectedTab === "From websites",
      onClick: () => setSelectedTab("From websites"),
      iconName: "graph",
    },
  ];

  return (
    <div className={styles.knowledge_to_feed_wrapper}>
      <div className={styles.single_selector_wrapper}>
        <SingleSelector
          options={brainsWithUploadRights}
          onChange={setCurrentBrainId}
          selectedOption={
            currentBrain
              ? { label: currentBrain.name, value: currentBrain.id }
              : undefined
          }
          placeholder="Select a brain"
        />
      </div>
      <Tabs tabList={knowledgesTabs} />
      <div className={styles.tabs_content_wrapper}>
        {selectedTab === "From documents" && <FromDocuments />}
        {selectedTab === "From websites" && <FromWebsites />}
      </div>
      {knowledgeToFeed.map((knowledge, index) => (
        <div key={index}>
          <h2>{knowledge.source}</h2>
        </div>
      ))}
    </div>
  );
};
