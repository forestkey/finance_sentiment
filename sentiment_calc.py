import torch
import yaml
import time
from tqdm import tqdm
from transformers import AutoTokenizer, BertModel, PreTrainedModel, PretrainedConfig
from transformers import BertForSequenceClassification 
from scrape_xueqiu_home import ScrapeXueqiuHome



class Dataset(torch.utils.data.Dataset):

    def __init__(self, text_path):
        # text_path = params['text_path']

        with open(text_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        self.lines = [d['outline'] for d in data]

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, i):
        return self.lines[i]
    

class SModel(PreTrainedModel):
    config_class = PretrainedConfig

    def __init__(self, config, params):
        super().__init__(config)
        self.params = params

        self.pretrained = BertModel.from_pretrained(self.params['model_hug_path'])
        self.dropout = torch.nn.Dropout(p=0.1)
        self.classifier = torch.nn.Linear(768, 2)

        #加载预训练模型的参数
        parameters = BertForSequenceClassification.from_pretrained(self.params['model_hug_path'], num_labels=2)
        self.dropout.load_state_dict(parameters.dropout.state_dict())
        self.classifier.load_state_dict(parameters.classifier.state_dict())

        self.criterion = torch.nn.CrossEntropyLoss()

    def forward(self, input_ids, attention_mask, labels=None):
        logits = self.pretrained(input_ids=input_ids,
                                 attention_mask=attention_mask)
        # logits = logits.last_hidden_state[:, 0]
        logits = logits[1]
        logits = self.classifier(self.dropout(logits))

        loss = None
        if labels is not None:
            loss = self.criterion(logits, labels)

        return {'loss': loss, 'logits': logits}


class SentimentCalc:
    def __init__(self, params):

        self.params = params
        self.model = SModel(PretrainedConfig(), params)

        #加载编码器
        self.tokenizer = AutoTokenizer.from_pretrained(self.params['model_hug_path'])

    def produce_loader(self, dataset):
        def collate_fn(data):
            data = self.tokenizer.batch_encode_plus(data,
                                            padding=True,
                                            truncation=True,
                                            max_length=self.params['max_length'],
                                            return_tensors='pt')

            data['labels'] = data['input_ids'].clone()

            return data


        #数据加载器
        loader = torch.utils.data.DataLoader(
            dataset=dataset,
            batch_size=self.params['batch_size'],
            collate_fn=collate_fn,
            shuffle=True,
            drop_last=True,
        )

        return loader
    
    def predict(self, dataset):
        loader = self.produce_loader(dataset)
        self.model.eval()
        with torch.no_grad():
            total_moods = None
            for i, data in tqdm(enumerate(loader)):
                out = self.model(data['input_ids'], data['attention_mask'])
                batch_moods = torch.nn.functional.softmax(out['logits'],dim=-1)[:, 1]
                if total_moods is None:
                    total_moods = batch_moods 
                else:
                    total_moods = torch.cat((total_moods, batch_moods), dim=0)

        return total_moods
    
    def xueqiu_home_sentiment(self):
        scrape = ScrapeXueqiuHome()

        time_str = time.strftime("%Y%m%d-%H%M%S", time.localtime()) 

        outlines_save_path = scrape.scrape(time_str, scroll_times=10, details=False)

        dataset = Dataset(outlines_save_path)

        return self.predict(dataset)
    

if __name__ == '__main__':
    params = {
        'model_hug_path': 'IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment',
        'batch_size' : 8,
        'max_length': 128,
    }

    # dataset = Dataset(params)
    sc = SentimentCalc(params)
    moods = sc.xueqiu_home_sentiment()
    print(moods)